"""Audit this project's F32 LoRA smoke archive without Torch or model execution."""
import argparse
import hashlib
import json
import math
import struct
import zipfile
from pathlib import Path, PurePosixPath

from valar_llm.contracts.requests import REQUEST
from valar_llm.data.fixtures import load_cases
from valar_llm.runtime.config import load_config
from valar_llm.runtime.prompts import messages_for


def inspect_tensors(data: bytes) -> dict:
    if len(data) < 8:
        raise ValueError("Truncated safetensors header")
    length = struct.unpack("<Q", data[:8])[0]
    if not 2 <= length <= min(1_000_000, len(data) - 8):
        raise ValueError("Invalid safetensors header length")
    header = json.loads(data[8:8 + length])
    payload = memoryview(data)[8 + length:]
    tensors = []
    ranges = []
    for name, item in header.items():
        if name == "__metadata__":
            continue
        if item["dtype"] != "F32":
            raise ValueError("This smoke auditor supports F32 adapter tensors only")
        shape = item["shape"]
        if not shape or any(type(d) is not int or d <= 0 for d in shape):
            raise ValueError("Invalid adapter tensor shape")
        start, end = item["data_offsets"]
        if not 0 <= start < end <= len(payload) or end - start != 4 * math.prod(shape):
            raise ValueError("Invalid adapter tensor offsets or byte count")
        count = nonzero = 0
        square_sum = 0.0
        for (value,) in struct.iter_unpack("<f", payload[start:end]):
            if not math.isfinite(value):
                raise ValueError("Nonfinite adapter weight")
            count += 1
            nonzero += value != 0
            square_sum += value * value
        ranges.append((start, end))
        tensors.append({"name": name, "shape": shape, "dtype": "F32", "elements": count,
                        "nonzero_elements": nonzero, "l2_norm": math.sqrt(square_sum)})
    cursor = 0
    for start, end in sorted(ranges):
        if start != cursor:
            raise ValueError("Overlapping or incomplete adapter tensor ranges")
        cursor = end
    if not tensors or cursor != len(payload):
        raise ValueError("Unaccounted adapter tensor payload")
    return {"tensor_count": len(tensors), "parameter_count": sum(t["elements"] for t in tensors),
            "all_weights_finite": True, "tensors": tensors}


def audit_archive(path: Path, expected_sha: str, config: dict) -> tuple[dict, dict]:
    actual = hashlib.sha256(path.read_bytes()).hexdigest()
    if actual != expected_sha.lower():
        raise ValueError("Adapter ZIP checksum mismatch")
    with zipfile.ZipFile(path) as archive:
        members = archive.infolist()
        if len(members) > 256 or sum(m.file_size for m in members) > 64_000_000:
            raise ValueError("Archive exceeds the smoke artifact budget")
        names = [m.filename for m in members]
        if len(names) != len(set(names)):
            raise ValueError("Duplicate archive members")
        for name in names:
            parts = PurePosixPath(name).parts
            if "\\" in name or ".." in parts or not parts or parts[0] != "smoke-adapter":
                raise ValueError("Unexpected archive path")
        if archive.testzip() is not None:
            raise ValueError("Corrupted ZIP member")
        prefix = "smoke-adapter/"
        required = ["valar-manifest.json", "adapter_config.json", "adapter_model.safetensors",
                    "mask-audit.json", "tokenizer.json", "preprocessor_config.json", "chat_template.jinja"]
        if not all(prefix + name in names for name in required):
            raise ValueError("Incomplete checkpoint or processor")
        manifest = json.loads(archive.read(prefix + "valar-manifest.json"))
        adapter = json.loads(archive.read(prefix + "adapter_config.json"))
        mask = json.loads(archive.read(prefix + "mask-audit.json"))
        if (manifest["model_id"] != config["model_id"] or manifest["revision"] != config["revision"]
                or adapter["base_model_name_or_path"] != config["model_id"]
                or adapter["r"] != config["lora_rank"] or adapter["init_lora_weights"] is not True):
            raise ValueError("Checkpoint base/revision/rank/initialization mismatch")
        if mask != manifest["mask_audit"] or not (
            mask["prefix_match"] and mask["image_tokens_masked"] and mask["has_pixel_values"]
            and mask["answer_tokens"] > 0
            and mask["total_tokens"] - mask["prompt_tokens"] == mask["answer_tokens"]
        ):
            raise ValueError("Inconsistent answer masking audit")
        case = next(c for c in load_cases() if c["id"] == manifest["fixture_id"])
        case_hash = hashlib.sha256(json.dumps(case, sort_keys=True).encode()).hexdigest()
        request = REQUEST.validate_python(case["request"])
        slots = ["IMAGE_SLOT"] * mask["image_count"]
        prompt_hash = hashlib.sha256(json.dumps(messages_for(request, slots), sort_keys=True).encode()).hexdigest()
        if manifest["fixture_sha256"] != case_hash or manifest["prompt_sha256"] != prompt_hash:
            raise ValueError("Fixture or prompt provenance mismatch")
        tensors = inspect_tensors(archive.read(prefix + "adapter_model.safetensors"))
        actual_tensors = {t["name"]: t for t in tensors["tensors"]}
        expected = {f"base_model.model.{module}.lora_{side}.weight"
                    for module in manifest["target_modules"] for side in ("A", "B")}
        if set(actual_tensors) != expected:
            raise ValueError("Adapter tensor coverage differs from intended target modules")
        b_tensors = []
        for module in manifest["target_modules"]:
            a = actual_tensors[f"base_model.model.{module}.lora_A.weight"]
            b = actual_tensors[f"base_model.model.{module}.lora_B.weight"]
            if len(a["shape"]) != 2 or len(b["shape"]) != 2 or (
                a["shape"][0] != adapter["r"] or b["shape"][1] != adapter["r"]
            ):
                raise ValueError("LoRA factor rank mismatch")
            if not b["nonzero_elements"]:
                raise ValueError("A saved LoRA-B factor remains entirely zero")
            b_tensors.append(b)
        hashes = {m.filename: hashlib.sha256(archive.read(m.filename)).hexdigest()
                  for m in members if not m.is_dir()}
    return {"kind": "offline_f32_smoke_checkpoint_audit", "archive_sha256": actual,
            "model_id": manifest["model_id"], "revision": manifest["revision"],
            "manifest_sha256": hashes[prefix + "valar-manifest.json"],
            "archive_members_sha256": hashes, "checks_passed": True,
            "target_modules": len(manifest["target_modules"]),
            "nonzero_lora_b_tensors": len(b_tensors), **tensors,
            "fresh_session_reload_verified": False, "held_out_quality_evaluated": False}, manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("archive", type=Path)
    parser.add_argument("--expected-sha256", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    manifest_path = args.output.with_name(args.output.stem + "-manifest.json")
    if args.output.exists() or manifest_path.exists():
        raise SystemExit("Use a new audit filename; preserve prior evidence")
    report, manifest = audit_archive(args.archive, args.expected_sha256, load_config())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "checks_passed", "archive_sha256", "tensor_count", "parameter_count",
        "target_modules", "nonzero_lora_b_tensors", "all_weights_finite"
    )}, indent=2))


if __name__ == "__main__":
    main()
