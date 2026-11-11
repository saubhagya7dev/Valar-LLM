import copy
import json

import pytest

from valar_llm.data.pilot import PILOT_ROOT, guideline_hash, load_pilot
from valar_llm.data.review import (
    ReviewDraft,
    events,
    make_packet,
    progress_report,
    record_review,
    validate_draft,
)


def context():
    return load_pilot()


def blank(item, reviewer="person_a"):
    manifest, report = context()
    return {"schema_version": "1", "dataset_sha256": report["manifest_sha256"],
            "item_id": item["id"], "item_sha256": item["sha256"], "reviewer_id": reviewer,
            "guideline_version": "1", "guideline_sha256": guideline_hash(),
            "review_method": "self_reported_human_blind", "action": "pending", "rubric": None,
            "notes": "", "elapsed_seconds_user_reported": None}


def vision_draft(reviewer="person_a"):
    manifest, _ = context()
    item = next(i for i in manifest["items"] if i["id"] == "P017")
    draft = blank(item, reviewer)
    draft.update(action="label", rubric={"role": "vision", "status": "supported",
        "claims": [{"text": "The Q1 operating cost is 187.5 USD thousands.", "citations": ["H1P1"]}]})
    return draft


def test_packet_is_allowlisted_and_has_no_default_label(tmp_path):
    manifest, report = context()
    item = manifest["items"][0]
    folder = make_packet(item, "person_a", manifest, report, PILOT_ROOT, tmp_path)
    evidence = json.loads((folder / "evidence.json").read_text())
    draft = json.loads((folder / "annotation.json").read_text())
    assert set(evidence) == {"item_id", "request", "pages", "attribution"}
    assert "coverage_tags" not in evidence and "transformation" not in evidence
    assert draft["action"] == "pending" and draft["rubric"] is None
    assert evidence["request"] == item["request"]
    with pytest.raises(ValueError, match="Pending"):
        validate_draft(draft, manifest, report)
    with pytest.raises(ValueError, match="preserve in-progress"):
        make_packet(item, "person_a", manifest, report, PILOT_ROOT, tmp_path)


def test_image_packet_copies_supplied_images_in_evidence_order(tmp_path):
    manifest, report = context()
    item = next(i for i in manifest["items"] if len(i["page_images"]) == 2)
    folder = make_packet(item, "person_a", manifest, report, PILOT_ROOT, tmp_path)
    packet = json.loads((folder / "evidence.json").read_text())
    assert [p["evidence_id"] for p in packet["pages"]] == [p["evidence_id"] for p in item["page_images"]]
    assert all((folder / p["file"]).is_file() for p in packet["pages"])


@pytest.mark.parametrize("field", ["dataset_sha256", "item_sha256", "guideline_sha256"])
def test_stale_review_is_rejected(field):
    manifest, report = context()
    draft = vision_draft()
    draft[field] = "0" * 64
    with pytest.raises(ValueError, match="stale"):
        validate_draft(draft, manifest, report)


def test_unknown_citation_is_not_accepted_as_human_gold():
    manifest, report = context()
    draft = vision_draft()
    draft["rubric"]["claims"][0]["citations"] = ["UNSUPPLIED"]
    with pytest.raises(ValueError, match="Unknown evidence"):
        validate_draft(draft, manifest, report)


def reviewer_draft():
    manifest, _ = context()
    item = next(i for i in manifest["items"] if i["id"] == "P003")
    draft = blank(item)
    draft.update(action="label", rubric={"role": "reviewer", "disposition": "needs_verification",
        "prerequisite_assessments": [{"prerequisite": "Deployment protection", "state": "unknown",
            "evidence_ids": ["E2"], "incident_ids": ["I1"], "reason": "The shown middleware does not establish deployment."}],
        "existing_defenses": [], "evidence_ids": ["E2"], "incident_ids": ["I1"],
        "missing_information": ["Deployment configuration"], "reason": "Deployment remains unknown."})
    return draft


def test_review_cannot_promote_unknown_prerequisite_or_invent_defense():
    manifest, report = context()
    draft = reviewer_draft()
    assert validate_draft(draft, manifest, report)
    promoted = copy.deepcopy(draft)
    promoted["rubric"]["disposition"] = "supported_concern"
    with pytest.raises(ValueError, match="Supported concern"):
        validate_draft(promoted, manifest, report)
    invented = copy.deepcopy(draft)
    invented["rubric"]["existing_defenses"] = [{"description": "A header guard", "evidence_ids": ["E999"]}]
    with pytest.raises(ValueError, match="Unknown annotation"):
        validate_draft(invented, manifest, report)


def test_extraction_quote_must_be_verbatim():
    manifest, report = context()
    item = manifest["items"][0]
    draft = blank(item)
    quote = item["request"]["payload"]["sources"][0]["passages"][0]
    draft.update(action="label", rubric={"role": "researcher", "record_type": "vulnerability_advisory",
        "mechanism": "A source-supported external behavior.", "prerequisites": [],
        "supporting_quotes": [{"source_id": "S1", "quote": quote}], "unknowns": []})
    assert validate_draft(draft, manifest, report)
    draft["rubric"]["supporting_quotes"][0]["quote"] = "Invented source sentence with no support anywhere in this input."
    with pytest.raises(ValueError, match="contiguous"):
        validate_draft(draft, manifest, report)


def test_review_records_are_append_only_and_require_explicit_revision(tmp_path):
    manifest, report = context()
    draft = vision_draft()
    first = record_review(draft, manifest, report, tmp_path)
    original = first.read_bytes()
    with pytest.raises(ValueError, match="supersedes"):
        record_review(draft, manifest, report, tmp_path)
    event = json.loads(first.read_text())
    revised = copy.deepcopy(draft)
    revised["notes"] = "Clarified after an explicitly recorded second look."
    second = record_review(revised, manifest, report, tmp_path, event["event_id"])
    assert second != first and first.read_bytes() == original
    assert len(events(manifest, report, tmp_path)) == 2
    assert progress_report(manifest, report, tmp_path)["items_with_a_label"] == 1


def test_modified_private_annotation_event_is_detected(tmp_path):
    manifest, report = context()
    path = record_review(vision_draft(), manifest, report, tmp_path)
    event = json.loads(path.read_text())
    event["annotation"]["notes"] = "Unrecorded edit"
    path.write_text(json.dumps(event))
    with pytest.raises(ValueError, match="event was modified"):
        events(manifest, report, tmp_path)


def test_disagreement_is_flagged_without_claiming_accuracy_or_independence(tmp_path):
    manifest, report = context()
    record_review(vision_draft(), manifest, report, tmp_path)
    other = vision_draft("person_b")
    other["rubric"] = {"role": "vision", "status": "insufficient", "claims": []}
    record_review(other, manifest, report, tmp_path)
    progress = progress_report(manifest, report, tmp_path)
    assert progress["primary_label_disagreements"] == ["P017"]
    assert not progress["independent_human_gold_verified"]
    assert progress["model_accuracy"] == "not measured"
    assert progress["agreement_statistic"] == "not measured"


def test_skipping_records_a_reason_without_a_provisional_label(tmp_path):
    manifest, report = context()
    draft = blank(manifest["items"][0])
    draft.update(action="skip", notes="Need more time for this source.")
    record_review(draft, manifest, report, tmp_path)
    progress = progress_report(manifest, report, tmp_path)
    assert progress["items_with_a_label"] == 0 and progress["review_actions"] == {"skip": 1}


def test_review_schema_export_matches_runtime():
    from pathlib import Path

    assert json.loads(Path("schemas/pilot-annotation.v1.json").read_text()) == ReviewDraft.model_json_schema()


def test_cli_does_not_echo_invalid_private_annotation_values(monkeypatch, tmp_path, capsys):
    import sys

    from valar_llm.cli import main

    draft = vision_draft()
    draft["rubric"]["status"] = "private-value-that-must-not-be-logged"
    path = tmp_path / "private-draft.json"
    path.write_text(json.dumps(draft))
    monkeypatch.setattr(sys, "argv", ["valar", "pilot", "record", str(path)])
    with pytest.raises(SystemExit) as exit_code:
        main()
    assert exit_code.value.code == 2
    error = capsys.readouterr().err
    assert "private-value-that-must-not-be-logged" not in error
    assert "Invalid pilot/review fields" in error
