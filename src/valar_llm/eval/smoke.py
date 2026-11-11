import argparse
import hashlib
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

from valar_llm.contracts.requests import REQUEST
from valar_llm.contracts.validation import validate_output
from valar_llm.data.fixtures import fixture_images, load_cases
from valar_llm.runtime.config import load_config
from valar_llm.runtime.model import generate, load_model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="configs/phase0.json")
    parser.add_argument("--adapter")
    parser.add_argument("--output", default="results/runs/base-smoke.json")
    parser.add_argument("--case", action="append", help="Repeat to select bounded smoke cases")
    args = parser.parse_args()
    if os.getenv("VALAR_FREE_ONLINE_RUNTIME") != "confirmed":
        raise SystemExit("Use a confirmed free online runtime")
    import torch

    config = load_config(args.config)
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Use a new result filename; previous measurements are immutable")
    load_start = time.perf_counter()
    model, processor = load_model(config, adapter=args.adapter)
    load_seconds = time.perf_counter() - load_start
    records = []
    selected = set(args.case or ["compact-advisory", "review-unknown", "vision-image"])
    cases = [c for c in load_cases() if c["id"] in selected]
    if len(cases) != len(selected):
        raise ValueError("Unknown smoke case selected")
    for case in cases:
        images = fixture_images(case)
        request = REQUEST.validate_python(case["request"])
        torch.cuda.synchronize()
        start = time.perf_counter()
        record = {"id": case["id"], "task": request.task, "contract_valid": False}
        try:
            prediction = generate(model, processor, request, images, config)
            validate_output(request, prediction)
            record.update(contract_valid=True, prediction=prediction)
        except (ValueError, TypeError) as exc:
            record["failure_type"] = type(exc).__name__
        finally:
            torch.cuda.synchronize()
            record["generation_seconds"] = time.perf_counter() - start
            for image in images:
                image.close()
        records.append(record)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({
        "kind": "synthetic_inference_smoke_not_quality_evaluation",
        "created_at": datetime.now(timezone.utc).isoformat(), "model_id": config["model_id"],
        "revision": config["revision"], "config": config,
        "adapter_manifest_sha256": hashlib.sha256(
            (Path(args.adapter) / "valar-manifest.json").read_bytes()).hexdigest()
        if args.adapter else None,
        "process_id": os.getpid(), "load_seconds": load_seconds,
        "gpu": torch.cuda.get_device_name(), "records": records,
        "semantic_support": "requires human review",
    }, indent=2) + "\n")
    print(f"Saved {len(records)} real inference attempts to {output}")


if __name__ == "__main__":
    main()
