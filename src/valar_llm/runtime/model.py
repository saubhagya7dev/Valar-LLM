import json
from pathlib import Path

from .output import parse_output
from .prompts import messages_for


def load_model(config, *, quantized=False, adapter=None, cpu=False):
    # GPU dependencies are intentionally absent from the offline package dependency graph.
    import torch
    from transformers import AutoProcessor, BitsAndBytesConfig, Qwen3VLForConditionalGeneration

    if not cpu and not torch.cuda.is_available():
        raise RuntimeError("GPU smoke runs require a free online CUDA runtime")
    dtype = torch.float16 if cpu or not torch.cuda.is_bf16_supported() else torch.bfloat16
    kwargs = dict(revision=config["revision"], torch_dtype=dtype,
                  trust_remote_code=False, attn_implementation="sdpa")
    if quantized:
        kwargs["quantization_config"] = BitsAndBytesConfig(
            load_in_4bit=True, bnb_4bit_quant_type="nf4", bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=dtype,
        )
    kwargs["device_map"] = "cpu" if cpu else {"": 0}
    processor = AutoProcessor.from_pretrained(
        config["model_id"], revision=config["revision"], trust_remote_code=False,
        max_pixels=config["processor_max_pixels"],
    )
    model = Qwen3VLForConditionalGeneration.from_pretrained(config["model_id"], **kwargs)
    if adapter:
        from peft import PeftModel

        manifest = json.loads((Path(adapter) / "valar-manifest.json").read_text())
        if manifest["model_id"] != config["model_id"] or manifest["revision"] != config["revision"]:
            raise ValueError("Adapter/base revision mismatch")
        model = PeftModel.from_pretrained(model, adapter)
    return model, processor


def encode(processor, messages, max_tokens, *, generation=True):
    # ProcessorMixin in Transformers 4.57.1 inspects every message's content
    # as multimodal blocks, including system and assistant text-only messages.
    # Tokenizer templates accept strings, but the processor's media scan does not.
    normalized = [
        {**message, "content": [{"type": "text", "text": message["content"]}]}
        if isinstance(message["content"], str) else message
        for message in messages
    ]
    batch = processor.apply_chat_template(
        normalized, tokenize=True, add_generation_prompt=generation,
        return_dict=True, return_tensors="pt",
    )
    if batch["input_ids"].shape[-1] > max_tokens:
        raise ValueError("Input exceeds token budget; never truncate image tokens")
    return batch


def generate(model, processor, request, images, config, *, diagnostics=None):
    import torch

    batch = encode(processor, messages_for(request, images), config["max_input_tokens"])
    batch = batch.to(model.device)
    model.eval()
    with torch.inference_mode():
        output = model.generate(**batch, max_new_tokens=config["max_new_tokens"], do_sample=False)
    text = processor.decode(output[0][batch["input_ids"].shape[-1]:], skip_special_tokens=True)
    # Exact fences are formatting only; no response fields or facts are repaired.
    # The smoke runner records raw JSON validity separately from normalized validity.
    return parse_output(text, diagnostics)
