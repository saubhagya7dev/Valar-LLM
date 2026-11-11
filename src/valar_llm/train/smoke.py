"""Run only inside a verified free online CUDA notebook; synthetic fixtures only."""
import argparse
import hashlib
import importlib.metadata
import json
import os
import platform
import time
from datetime import datetime, timezone
from pathlib import Path

from valar_llm.contracts.requests import REQUEST
from valar_llm.contracts.validation import validate_output
from valar_llm.data.fixtures import fixture_images, load_cases
from valar_llm.runtime.config import load_config
from valar_llm.runtime.model import encode, load_model
from valar_llm.runtime.prompts import messages_for


def answer_boundary(full_ids: list[int], prompt_ids: list[int]) -> int:
    """Require an exact template prefix, including image positions, before masking loss."""
    length = len(prompt_ids)
    if not length or length >= len(full_ids) or full_ids[:length] != prompt_ids:
        raise ValueError("Template prefix mismatch or no answer tokens; inspect before training")
    return length


def mask_answer(full_ids, prompt_ids):
    """The smoke deliberately accepts one example, avoiding padding/batching ambiguity."""
    if full_ids.shape[0] != 1 or prompt_ids.shape[0] != 1:
        raise ValueError("The masking smoke requires batch size one")
    length = answer_boundary(full_ids[0].tolist(), prompt_ids[0].tolist())
    labels = full_ids.clone()
    labels[:, :length] = -100
    return labels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/phase0.json")
    parser.add_argument("--case", default="vision-image")
    parser.add_argument("--output", default="artifacts/smoke-adapter")
    args = parser.parse_args()
    if os.getenv("VALAR_FREE_ONLINE_RUNTIME") != "confirmed":
        raise SystemExit("Confirm a free online runtime with VALAR_FREE_ONLINE_RUNTIME=confirmed")
    import torch
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training

    config = load_config(args.config)
    torch.manual_seed(config["seed"])
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(config["seed"])
    case = next(c for c in load_cases() if c["id"] == args.case)
    request = REQUEST.validate_python(case["request"])
    validate_output(request, case["expected"])
    images = fixture_images(case)
    output = Path(args.output)
    if output.exists() and any(output.iterdir()):
        raise SystemExit("Choose a new output directory; do not overwrite previous experiments")
    output.mkdir(parents=True, exist_ok=True)
    try:
        model, processor = load_model(config, quantized=True)
        model = prepare_model_for_kbit_training(model)
        # Explicit text-tower projections: avoid silently adapting the vision tower.
        modules = [name for name, _ in model.named_modules()
                   if ".language_model." in name and name.endswith(("q_proj", "v_proj"))]
        if not modules:
            raise RuntimeError("No text-tower LoRA targets found; inspect the pinned architecture")
        model = get_peft_model(model, LoraConfig(
            r=config["lora_rank"], lora_alpha=2 * config["lora_rank"],
            lora_dropout=0.0, target_modules=modules, task_type="CAUSAL_LM",
        ))
        messages = messages_for(request, images)
        prompt = encode(processor, messages, config["max_input_tokens"])
        answer = json.dumps(case["expected"], ensure_ascii=False)
        complete = messages + [{"role": "assistant", "content": answer}]
        batch = encode(processor, complete, config["max_input_tokens"], generation=False)
        labels = mask_answer(batch["input_ids"], prompt["input_ids"])
        if images and ("pixel_values" not in batch or "image_grid_thw" not in batch):
            raise RuntimeError("Multimodal processor dropped image inputs")
        # The exact prefix includes every image token, so all image tokens have masked loss.
        audit = {"prompt_tokens": prompt["input_ids"].shape[-1],
                 "total_tokens": batch["input_ids"].shape[-1],
                 "answer_tokens": int((labels != -100).sum()),
                 "image_count": len(images), "has_pixel_values": "pixel_values" in batch,
                 "prefix_match": True, "image_tokens_masked": True}
        (output / "mask-audit.json").write_text(json.dumps(audit, indent=2) + "\n")
        batch["labels"] = labels
        batch = batch.to(model.device)
        optimizer = torch.optim.AdamW((p for p in model.parameters() if p.requires_grad),
                                      lr=config["learning_rate"])
        model.config.use_cache = False
        model.train()
        torch.cuda.reset_peak_memory_stats()
        steps = []
        for step in range(config["training_steps"]):
            torch.cuda.synchronize()
            start = time.perf_counter()
            optimizer.zero_grad(set_to_none=True)
            loss = model(**batch).loss
            if not torch.isfinite(loss):
                raise RuntimeError("Nonfinite smoke loss; checkpoint not accepted")
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            torch.cuda.synchronize()
            steps.append({"step": step + 1, "loss": loss.item(),
                          "seconds": time.perf_counter() - start})
            # Tiny runs save each step; full optimizer-resume is outside this smoke workflow.
            model.save_pretrained(output, safe_serialization=True)
        processor.save_pretrained(output)
        manifest = {"kind": "synthetic_training_smoke_not_quality_evidence",
                    "created_at": datetime.now(timezone.utc).isoformat(),
                    "model_id": config["model_id"], "revision": config["revision"],
                    "config": config, "fixture_id": case["id"],
                    "fixture_sha256": hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest(),
                    "prompt_sha256": hashlib.sha256(json.dumps(messages_for(request, [] if not images else
                        ["IMAGE_SLOT"] * len(images)), sort_keys=True).encode()).hexdigest(),
                    "steps": steps, "mask_audit": audit, "target_modules": modules,
                    "gpu": torch.cuda.get_device_name(),
                    "peak_allocated_bytes": torch.cuda.max_memory_allocated(),
                    "python": platform.python_version(),
                    "packages": {p: importlib.metadata.version(p) for p in
                                 ("torch", "transformers", "peft", "accelerate", "bitsandbytes", "pillow")}}
        (output / "valar-manifest.json").write_text(json.dumps(manifest, indent=2) + "\n")
        print(f"Saved {len(steps)} measured smoke steps to {output}. Persist externally before restart.")
    finally:
        for image in images:
            image.close()


if __name__ == "__main__":
    main()
