import copy
import json
import shutil

import pytest

from valar_llm.data.pilot import (
    PILOT_ROOT,
    PilotManifest,
    check_partition_leakage,
    digest,
    item_hash,
    load_pilot,
    safe_path,
)


def test_batch_is_unlabeled_development_only_with_grouped_families():
    manifest, report = load_pilot()
    assert report["items"] == 24
    assert report["families"] == 8
    assert report["partitions"] == {"development": 24, "train": 0, "test": 0}
    assert report["human_labels_in_manifest"] == 0
    assert not report["model_executed"] and not report["training_export_available"]
    assert {i["review_state"] for i in manifest["items"]} == {"unlabeled"}
    assert len([s for s in manifest["sources"] if s["license"] == "CC-BY-4.0"]) == 3
    assert not report["near_duplicate_warnings"]


@pytest.mark.parametrize("field", ["expected", "teacher_output", "prediction"])
def test_manifest_rejects_embedded_answer_keys(field):
    manifest = json.loads((PILOT_ROOT / "manifest.json").read_text())
    manifest["items"][0][field] = {"record_type": "a proposed answer"}
    with pytest.raises(ValueError):
        PilotManifest.model_validate(manifest)


def copy_batch(tmp_path):
    root = tmp_path / "pilot"
    shutil.copytree(PILOT_ROOT, root)
    return root


def rewrite_manifest(root, manifest):
    (root / "manifest.json").write_text(json.dumps(manifest))
    (root / "splits.json").write_text(json.dumps({"manifest_sha256": digest(manifest),
        "family_splits": manifest["family_splits"], "train": [], "test": [],
        "development": [i["id"] for i in manifest["items"]]}))


def test_modified_source_bytes_are_rejected(tmp_path):
    root = copy_batch(tmp_path)
    path = next((root / "sources").glob("GHSA-*.json"))
    path.write_bytes(path.read_bytes() + b" ")
    with pytest.raises(ValueError, match="Source snapshot changed"):
        load_pilot(root)


def test_changed_page_identity_rejected_even_after_rehashing_item(tmp_path):
    root = copy_batch(tmp_path)
    manifest = json.loads((root / "manifest.json").read_text())
    item = next(i for i in manifest["items"] if i["request"]["task"] == "vision.answer")
    item["request"]["payload"]["evidence"][0]["version_id"] = "different-version"
    item["sha256"] = item_hash(item, {a["id"]: a for a in manifest["assets"]})
    rewrite_manifest(root, manifest)
    with pytest.raises(ValueError, match="Immutable page"):
        load_pilot(root)


def test_split_manifest_is_not_silently_reassigned(tmp_path):
    root = copy_batch(tmp_path)
    split = json.loads((root / "splits.json").read_text())
    split["test"] = [split["development"].pop()]
    (root / "splits.json").write_text(json.dumps(split))
    with pytest.raises(ValueError, match="Split manifest"):
        load_pilot(root)


def test_reused_smoke_request_is_excluded(tmp_path):
    from valar_llm.data.fixtures import load_cases

    root = copy_batch(tmp_path)
    manifest = json.loads((root / "manifest.json").read_text())
    manifest["items"][0]["request"] = copy.deepcopy(next(c["request"] for c in load_cases()
                                                        if c["id"] == "compact-advisory"))
    rewrite_manifest(root, manifest)
    with pytest.raises(ValueError, match="Smoke request"):
        load_pilot(root)


def test_enriched_reviewer_input_cannot_smuggle_cached_model_predictions(tmp_path):
    root = copy_batch(tmp_path)
    manifest = json.loads((root / "manifest.json").read_text())
    item = next(i for i in manifest["items"] if i["request"]["task"] == "reviewer")
    item["request"]["payload"]["research"]["incidents"][0]["prediction"] = {"answer": "suggested label"}
    rewrite_manifest(root, manifest)
    with pytest.raises(ValueError, match="answer metadata"):
        load_pilot(root)


@pytest.mark.parametrize("reason", ["family", "image", "near-text"])
def test_cross_task_leakage_cannot_cross_partitions(reason):
    first = {"id": "a", "family": "one", "split": "development", "content_hashes": [], "texts": []}
    second = {"id": "b", "family": "two", "split": "test", "content_hashes": [], "texts": []}
    if reason == "family":
        second["family"] = "one"
    elif reason == "image":
        first["content_hashes"] = second["content_hashes"] = ["same-decoded-page"]
    else:
        passage = " ".join(f"word{x}" for x in range(100))
        first["texts"] = [passage]
        second["texts"] = [passage + " slight variation"]
    with pytest.raises(ValueError, match="crosses partitions"):
        check_partition_leakage([first, second])


def test_same_development_family_can_have_related_variants():
    assert check_partition_leakage([
        {"id": "a", "family": "one", "split": "development", "content_hashes": ["image"]},
        {"id": "b", "family": "one", "split": "development", "content_hashes": ["image"]},
    ]) == []


def test_asset_paths_cannot_escape_dataset(tmp_path):
    with pytest.raises(ValueError, match="escapes"):
        safe_path(tmp_path, "../private-file")
