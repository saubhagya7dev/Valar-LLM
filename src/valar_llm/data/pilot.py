"""Development-only pilot manifests with provenance, image identity and leakage checks."""
import hashlib
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path
from typing import Literal

from PIL import Image
from pydantic import Field

from valar_llm.contracts.requests import REQUEST, StrictModel
from valar_llm.data.fixtures import fixture_images, load_cases

PILOT_ROOT = Path("data/pilot/v1")
GUIDES = ("docs/labeling/shared.md", "docs/labeling/researcher.md",
          "docs/labeling/reviewer.md", "docs/labeling/vision.md")


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode()).hexdigest()


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def safe_path(root: Path, relative: str) -> Path:
    path = (root / relative).resolve()
    if not path.is_relative_to(root.resolve()) or Path(relative).is_absolute():
        raise ValueError("Pilot asset/source path escapes its dataset")
    return path


def pixel_hash(path: Path) -> str:
    with Image.open(path) as image:
        if image.width * image.height > 1_048_576:
            raise ValueError("Pilot image exceeds pixel budget")
        rgb = image.convert("RGB")
        return hashlib.sha256(f"{rgb.width}x{rgb.height}:".encode() + rgb.tobytes()).hexdigest()


def guideline_hash() -> str:
    return digest({name: file_hash(Path(name)) for name in GUIDES})


class PilotSource(StrictModel):
    id: str
    family: str
    file: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    license: Literal["CC-BY-4.0", "CC0-1.0"]
    attribution: str = Field(min_length=1)
    url: str
    license_url: str
    revision: str
    transformation: str


class PilotAsset(StrictModel):
    id: str
    family: str
    source_id: str
    file: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    pixel_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    version_id: str
    page: int = Field(ge=1)
    preprocessing: str


class PageLink(StrictModel):
    evidence_id: str
    asset_id: str


class PilotItem(StrictModel):
    id: str = Field(pattern=r"^P[0-9]{3}$")
    family: str
    split: Literal["development"]
    source_ids: list[str] = Field(min_length=1)
    request: dict
    page_images: list[PageLink] = Field(default_factory=list)
    coverage_tags: list[str]
    transformation: str
    review_state: Literal["unlabeled"] = "unlabeled"
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class PilotManifest(StrictModel):
    schema_version: Literal["1"]
    dataset_id: Literal["pilot-dev-v1"]
    purpose: Literal["development_only_no_training_export"]
    created_on: str
    guideline_version: Literal["1"]
    family_splits: dict[str, Literal["development"]]
    license_files: dict[str, str]
    sources: list[PilotSource]
    assets: list[PilotAsset]
    items: list[PilotItem]


def item_hash(item: dict, assets: dict) -> str:
    return digest({"request": item["request"], "family": item["family"], "split": item["split"],
                   "source_ids": item["source_ids"], "pages": [
                       {"evidence_id": p["evidence_id"], "asset_sha256": assets[p["asset_id"]]["sha256"]}
                       for p in item["page_images"]]})


def normalized_text(text: str) -> str:
    return " ".join(re.findall(r"\w+", unicodedata.normalize("NFKC", text).casefold()))


def shingles(text: str) -> set[tuple]:
    words = normalized_text(text).split()
    return {tuple(words[n:n + 5]) for n in range(max(0, len(words) - 4))}


def check_partition_leakage(records: list[dict]) -> list[dict]:
    """Shared families/assets/text cannot cross partitions, even across task IDs."""
    families, hashes = {}, {}
    passages = []
    warnings = []
    for item in records:
        split, family = item["split"], item["family"]
        if family in families and families[family] != split:
            raise ValueError("Source family crosses partitions")
        families[family] = split
        for key in item.get("content_hashes", []):
            if key in hashes and hashes[key] != split:
                raise ValueError("Identical content crosses partitions")
            hashes[key] = split
        for text in item.get("texts", []):
            tokens = shingles(text)
            if len(tokens) < 8:
                continue
            for previous, other in passages:
                similarity = len(tokens & other) / len(tokens | other)
                if similarity >= 0.8 and previous["family"] != family:
                    if previous["split"] != split:
                        raise ValueError("Near-duplicate evidence crosses partitions")
                    warnings.append({"items": [previous["id"], item["id"]],
                                     "reason": "near-duplicate evidence; review family grouping"})
            passages.append((item, tokens))
    return warnings


def evidence_texts(request: dict) -> list[str]:
    payload = request["payload"]
    return ([p for s in payload.get("sources", []) for p in s["passages"]]
            + [i["source_quote"] for i in payload.get("research", {}).get("incidents", [])]
            + [o["quote"] for o in payload.get("profile", {}).get("observations", [])]
            + [e["text"] for e in payload.get("evidence", []) if e["text"]])


def reject_answer_metadata(value):
    if isinstance(value, dict):
        if set(value) & {"expected", "expected_output", "prediction", "teacher_output",
                         "gold_label", "model_output", "candidate_response"}:
            raise ValueError("Model/target answer metadata is not permitted in pilot evidence")
        for child in value.values():
            reject_answer_metadata(child)
    elif isinstance(value, list):
        for child in value:
            reject_answer_metadata(child)


def load_pilot(root: Path = PILOT_ROOT) -> tuple[dict, dict]:
    path = root / "manifest.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    manifest = PilotManifest.model_validate(raw).model_dump()
    for group in ("sources", "assets", "items"):
        ids = [x["id"] for x in manifest[group]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate pilot identifiers")
    sources = {s["id"]: s for s in manifest["sources"]}
    assets = {a["id"]: a for a in manifest["assets"]}
    for name, expected in manifest["license_files"].items():
        if file_hash(safe_path(root, name)) != expected:
            raise ValueError("License snapshot changed")
    for source in sources.values():
        if file_hash(safe_path(root, source["file"])) != source["sha256"]:
            raise ValueError("Source snapshot changed")
        if source["license"] == "CC-BY-4.0" and not re.fullmatch(r"[a-f0-9]{40}", source["revision"]):
            raise ValueError("External advisory requires an immutable revision")
        if not source["license_url"].startswith("https://"):
            raise ValueError("Missing license reference")
    for asset in assets.values():
        path = safe_path(root, asset["file"])
        if file_hash(path) != asset["sha256"] or pixel_hash(path) != asset["pixel_sha256"]:
            raise ValueError("Page bytes or decoded pixels changed")
        if sources[asset["source_id"]]["family"] != asset["family"]:
            raise ValueError("Page source-family mismatch")
    smoke_requests = {digest(REQUEST.validate_python(c["request"]).model_dump()) for c in load_cases()}
    smoke_pixels = set()
    for case in load_cases():
        for image in fixture_images(case):
            smoke_pixels.add(hashlib.sha256(f"{image.width}x{image.height}:".encode()
                                           + image.tobytes()).hexdigest())
            image.close()
    smoke_texts = [t for c in load_cases() for t in evidence_texts(c["request"]) if len(t) >= 60]
    smoke_text_hashes = {digest(normalized_text(t)) for t in smoke_texts}
    partitions = []
    unique_requests = set()
    for item in manifest["items"]:
        reject_answer_metadata(item["request"])
        request = REQUEST.validate_python(item["request"])
        if digest(request.model_dump()) in smoke_requests:
            raise ValueError("Smoke request cannot be presented as new pilot data")
        if item["sha256"] != item_hash(item, assets):
            raise ValueError("Pilot request or page identity changed")
        if manifest["family_splits"].get(item["family"]) != item["split"]:
            raise ValueError("Missing or inconsistent source-family assignment")
        if any(sources[s]["family"] != item["family"] for s in item["source_ids"]):
            raise ValueError("Related source family is not grouped with its item")
        evidence = getattr(request.payload, "evidence", [])
        if len(evidence) != len(item["page_images"]):
            raise ValueError("Pilot image/evidence count mismatch")
        image_hashes = []
        for entry, page in zip(evidence, item["page_images"]):
            asset = assets[page["asset_id"]]
            if (entry.id != page["evidence_id"] or entry.version_id != asset["version_id"]
                    or entry.page != asset["page"] or asset["family"] != item["family"]):
                raise ValueError("Immutable page/evidence association mismatch")
            if asset["pixel_sha256"] in smoke_pixels:
                raise ValueError("Smoke image cannot be presented as new pilot evidence")
            image_hashes.append(asset["pixel_sha256"])
        key = digest({"request": request.model_dump(), "images": image_hashes})
        if key in unique_requests:
            raise ValueError("Exact duplicate pilot request")
        unique_requests.add(key)
        texts = evidence_texts(item["request"])
        for text in texts:
            if len(text) >= 60 and digest(normalized_text(text)) in smoke_text_hashes:
                raise ValueError("Smoke evidence cannot be presented as new pilot material")
        partitions.append({"id": item["id"], "family": item["family"], "split": item["split"],
                           "texts": texts, "content_hashes": image_hashes + [key]
                           + [digest(normalized_text(t)) for t in texts if len(t) >= 60]})
    warnings = check_partition_leakage(partitions)
    split_manifest = json.loads((root / "splits.json").read_text(encoding="utf-8"))
    expected_split = {"manifest_sha256": digest(manifest), "family_splits": manifest["family_splits"],
                      "train": [], "test": [], "development": [i["id"] for i in manifest["items"]]}
    if split_manifest != expected_split:
        raise ValueError("Split manifest differs from the frozen development assignment")
    return manifest, {"dataset_id": manifest["dataset_id"], "manifest_sha256": digest(manifest),
                      "items": len(manifest["items"]), "families": len(manifest["family_splits"]),
                      "by_task": dict(Counter(i["request"]["task"] for i in manifest["items"])),
                      "partitions": {"development": len(manifest["items"]), "train": 0, "test": 0},
                      "human_labels_in_manifest": 0, "near_duplicate_warnings": warnings,
                      "model_executed": False, "training_export_available": False}
