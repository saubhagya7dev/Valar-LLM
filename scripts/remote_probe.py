"""Run from a separate free cloud notebook; secrets come from its environment only."""
import argparse
import json
import os
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path

from gradio_client import Client, handle_file

from valar_llm.contracts.requests import REQUEST
from valar_llm.contracts.validation import validate_output
from valar_llm.data.fixtures import fixture_images, load_cases


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("space", help="owner/space-name")
    parser.add_argument("--output", default="results/runs/remote-smoke.json")
    parser.add_argument("--base-only", action="store_true", help="Do not require an adapter identity")
    args = parser.parse_args()
    key = os.environ.get("VALAR_API_KEY")
    if not key:
        raise SystemExit("Set VALAR_API_KEY in this cloud client's secret environment")
    output = Path(args.output)
    if output.exists():
        raise SystemExit("Choose a new result filename")
    client = Client(args.space, hf_token=os.getenv("HF_TOKEN"), verbose=False)
    rows = []
    for identifier in ("compact-advisory", "review-unknown", "vision-image"):
        case = next(c for c in load_cases() if c["id"] == identifier)
        request = REQUEST.validate_python(case["request"])
        images = fixture_images(case)
        with tempfile.TemporaryDirectory() as tmp:
            uploads = []
            try:
                for index, image in enumerate(images):
                    path = Path(tmp) / f"page-{index}.png"
                    image.save(path)
                    uploads.append(handle_file(str(path)))
                start = time.perf_counter()
                row = {"id": identifier, "contract_valid": False}
                try:
                    result = client.predict(key, json.dumps(case["request"]), uploads or None,
                                            api_name="/predict")
                    row["status"] = result.get("status")
                    if result.get("status") == "ok":
                        validate_output(request, result["output"])
                        if not args.base_only and not result.get("adapter_manifest_sha256"):
                            raise ValueError("Adapter-serving probe received base-only inference")
                        row.update(contract_valid=True, prediction=result["output"],
                                   model_revision=result["model_revision"],
                                   adapter_manifest_sha256=result.get("adapter_manifest_sha256"))
                except Exception as exc:
                    row.update(status="probe_failure", failure_type=type(exc).__name__)
                row["elapsed_including_queue_seconds"] = time.perf_counter() - start
                rows.append(row)
            finally:
                for image in images:
                    image.close()
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"kind": "remote_synthetic_smoke", "space": args.space,
        "created_at": datetime.now(timezone.utc).isoformat(), "records": rows,
        "semantic_support": "human review required", "laptop_off_verification": "record separately"},
        indent=2) + "\n")
    print(output)


if __name__ == "__main__":
    main()
