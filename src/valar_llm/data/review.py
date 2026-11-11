"""Blind, local human-review packets and append-only development annotations."""
import json
import re
import shutil
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Annotated, Literal

from pydantic import Field

from valar_llm.contracts.requests import REQUEST, StrictModel
from valar_llm.contracts.validation import validate_output
from valar_llm.data.pilot import PILOT_ROOT, digest, guideline_hash, load_pilot, safe_path

PRIVATE = Path("data/private/annotations")


class SupportQuote(StrictModel):
    source_id: str
    quote: str = Field(min_length=40, max_length=800)


class ResearchLabel(StrictModel):
    role: Literal["researcher"]
    record_type: Literal["observed_attack", "vulnerability_advisory", "background_guidance", "insufficient_evidence"]
    mechanism: str = Field(max_length=1000)
    prerequisites: list[str] = Field(max_length=6)
    supporting_quotes: list[SupportQuote] = Field(max_length=6)
    unknowns: list[str] = Field(max_length=8)


class PrerequisiteLabel(StrictModel):
    prerequisite: str = Field(min_length=1, max_length=500)
    state: Literal["supported", "contradicted", "unknown"]
    evidence_ids: list[str]
    incident_ids: list[str]
    reason: str = Field(min_length=1, max_length=2000)


class DefenseLabel(StrictModel):
    description: str = Field(min_length=1, max_length=1000)
    evidence_ids: list[str] = Field(min_length=1)


class ReviewerLabel(StrictModel):
    role: Literal["reviewer"]
    disposition: Literal["supported_concern", "needs_verification", "background_lesson", "reject_match", "insufficient_context"]
    prerequisite_assessments: list[PrerequisiteLabel] = Field(max_length=8)
    existing_defenses: list[DefenseLabel] = Field(max_length=8)
    evidence_ids: list[str]
    incident_ids: list[str]
    missing_information: list[str] = Field(max_length=8)
    reason: str = Field(min_length=1, max_length=4000)


class ClaimLabel(StrictModel):
    text: str = Field(min_length=1, max_length=4000)
    citations: list[str] = Field(min_length=1, max_length=12)


class VisionLabel(StrictModel):
    role: Literal["vision"]
    status: Literal["supported", "insufficient", "conflicting"]
    claims: list[ClaimLabel] = Field(max_length=30)


Rubric = Annotated[ResearchLabel | ReviewerLabel | VisionLabel, Field(discriminator="role")]


class ReviewDraft(StrictModel):
    schema_version: Literal["1"]
    dataset_sha256: str
    item_id: str = Field(pattern=r"^P[0-9]{3}$")
    item_sha256: str
    reviewer_id: str = Field(pattern=r"^[A-Za-z0-9_-]{1,64}$")
    guideline_version: Literal["1"]
    guideline_sha256: str
    review_method: Literal["self_reported_human_blind"]
    action: Literal["pending", "label", "skip", "needs_adjudication"]
    rubric: Rubric | None
    notes: str = Field(max_length=5000)
    elapsed_seconds_user_reported: float | None = Field(default=None, ge=0)


def validate_draft(value: dict, manifest: dict, report: dict) -> dict:
    draft = ReviewDraft.model_validate(value)
    item = next((i for i in manifest["items"] if i["id"] == draft.item_id), None)
    if item is None or (draft.dataset_sha256 != report["manifest_sha256"]
                        or draft.item_sha256 != item["sha256"]
                        or draft.guideline_sha256 != guideline_hash()):
        raise ValueError("Annotation is stale or belongs to different evidence/guidelines")
    if draft.action == "pending":
        raise ValueError("Pending draft is not a completed review")
    if draft.action != "label":
        if draft.rubric is not None or not draft.notes.strip():
            raise ValueError("Skip/adjudication requires a reason and no provisional label")
        return draft.model_dump()
    rubric = draft.rubric
    if rubric is None:
        raise ValueError("A label requires a completed rubric")
    task, payload = item["request"]["task"], item["request"]["payload"]
    role = "researcher" if task.startswith("researcher") else "vision" if task == "vision.answer" else "reviewer"
    if rubric.role != role:
        raise ValueError("Annotation rubric does not match the task")
    if isinstance(rubric, ResearchLabel):
        sources = {s["id"]: s for s in payload["sources"]}
        if rubric.record_type == "insufficient_evidence":
            if rubric.mechanism or rubric.prerequisites or rubric.supporting_quotes:
                raise ValueError("Insufficient extraction must abstain from mechanism/prerequisite claims")
        elif not rubric.mechanism.strip() or not rubric.supporting_quotes:
            raise ValueError("A supported extraction requires a mechanism and source quote")
        for quote in rubric.supporting_quotes:
            source = sources.get(quote.source_id)
            if source is None or not any(quote.quote in p for p in source["passages"]):
                raise ValueError("Human support quote must be contiguous in the supplied source")
    elif isinstance(rubric, VisionLabel):
        validate_output(REQUEST.validate_python(item["request"]),
                        {"status": rubric.status, "claims": [c.model_dump() for c in rubric.claims]})
    else:
        observations = {o["id"]: o for o in payload["profile"]["observations"]}
        incidents = {i["id"] for i in payload["research"]["incidents"]}

        def refs(evidence, research):
            if not set(evidence) <= observations.keys() or not set(research) <= incidents:
                raise ValueError("Unknown annotation evidence or incident ID")

        refs(rubric.evidence_ids, rubric.incident_ids)
        for defense in rubric.existing_defenses:
            refs(defense.evidence_ids, [])
            if not any(observations[e]["kind"] == "observed" for e in defense.evidence_ids):
                raise ValueError("Existing defense requires observed repository evidence")
        for assessment in rubric.prerequisite_assessments:
            refs(assessment.evidence_ids, assessment.incident_ids)
            if assessment.state == "supported" and (
                not assessment.incident_ids or not assessment.evidence_ids
                or not any(observations[e]["kind"] == "observed" for e in assessment.evidence_ids)
            ):
                raise ValueError("Supported prerequisite requires direct observed evidence and incident IDs")
        states = {a.state for a in rubric.prerequisite_assessments}
        if rubric.disposition == "supported_concern" and (
            states != {"supported"} or rubric.missing_information
            or not rubric.evidence_ids or not rubric.incident_ids
        ):
            raise ValueError("Supported concern cannot have unknown, contradicted or missing prerequisites")
        if "contradicted" in states and rubric.disposition != "reject_match":
            raise ValueError("Contradicted material prerequisite rejects the match")
        if "unknown" in states and rubric.disposition not in {"needs_verification", "reject_match", "insufficient_context"}:
            raise ValueError("Unknown prerequisite cannot become a supported concern")
        if rubric.disposition == "needs_verification" and "unknown" not in states and not rubric.missing_information:
            raise ValueError("Needs verification must identify an unknown prerequisite or missing fact")
    return draft.model_dump()


def events(manifest: dict, report: dict, directory: Path = PRIVATE) -> list[dict]:
    result = []
    for path in sorted((directory / manifest["dataset_id"]).rglob("*.json")):
        event = json.loads(path.read_text(encoding="utf-8"))
        validate_draft(event["annotation"], manifest, report)
        if event["annotation_sha256"] != digest(event["annotation"]):
            raise ValueError("Annotation event was modified")
        result.append(event)
    # Events are an append-only linear history per reviewer/item, not an automatic consensus.
    by_id = {event["event_id"]: event for event in result}
    if len(by_id) != len(result):
        raise ValueError("Duplicate review event identity")
    for event in result:
        previous = event["supersedes"]
        if previous is not None and previous not in by_id:
            raise ValueError("Missing superseded review event")
        if previous is not None:
            before, after = by_id[previous]["annotation"], event["annotation"]
            if (before["reviewer_id"], before["item_id"]) != (after["reviewer_id"], after["item_id"]):
                raise ValueError("Review revision cannot supersede another reviewer or item")
        visited = {event["event_id"]}
        while previous is not None:
            if previous in visited:
                raise ValueError("Cycle in review revision history")
            visited.add(previous)
            previous = by_id[previous]["supersedes"]
    return sorted(result, key=lambda e: (e["created_at"], e["event_id"]))


def latest_events(history: list[dict]) -> dict:
    superseded = {e["supersedes"] for e in history if e["supersedes"]}
    latest = {}
    for event in history:
        if event["event_id"] not in superseded:
            annotation = event["annotation"]
            key = annotation["reviewer_id"], annotation["item_id"]
            if key in latest:
                raise ValueError("Conflicting review revisions require explicit adjudication")
            latest[key] = event
    return latest


def record_review(value: dict, manifest: dict, report: dict, directory: Path = PRIVATE,
                  supersedes: str | None = None) -> Path:
    annotation = validate_draft(value, manifest, report)
    previous = latest_events(events(manifest, report, directory)).get(
        (annotation["reviewer_id"], annotation["item_id"]))
    if (previous is None and supersedes is not None) or (
        previous is not None and supersedes != previous["event_id"]
    ):
        raise ValueError("Existing review requires its explicit --supersedes event ID")
    event_id = uuid.uuid4().hex
    event = {"event_id": event_id, "created_at": datetime.now(timezone.utc).isoformat(),
             "supersedes": supersedes, "annotation_sha256": digest(annotation),
             "annotation": annotation}
    path = directory / manifest["dataset_id"] / annotation["reviewer_id"] / (event_id + ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(event, indent=2) + "\n")
    return path


def make_packet(item: dict, reviewer: str, manifest: dict, report: dict, root: Path,
                output: Path) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", reviewer):
        raise ValueError("Use a short reviewer pseudonym containing letters, digits, _ or -")
    folder = output / reviewer / item["id"]
    if folder.exists():
        raise ValueError("Packet exists; preserve in-progress edits or use another output directory")
    folder.mkdir(parents=True)
    assets = {a["id"]: a for a in manifest["assets"]}
    pages = []
    for index, page in enumerate(item["page_images"]):
        destination = folder / f"page-{index + 1}.png"
        shutil.copyfile(safe_path(root, assets[page["asset_id"]]["file"]), destination)
        pages.append({"evidence_id": page["evidence_id"], "file": destination.name})
    sources = [{k: source[k] for k in ("id", "license", "attribution", "url", "license_url")}
               for source in manifest["sources"] if source["id"] in item["source_ids"]]
    # Allowlist fields: no curation tags, expected labels, cached predictions or teacher files.
    public = {"item_id": item["id"], "request": item["request"], "pages": pages, "attribution": sources}
    (folder / "evidence.json").write_text(json.dumps(public, indent=2) + "\n", encoding="utf-8")
    draft = {"schema_version": "1", "dataset_sha256": report["manifest_sha256"],
             "item_id": item["id"], "item_sha256": item["sha256"], "reviewer_id": reviewer,
             "guideline_version": "1", "guideline_sha256": guideline_hash(),
             "review_method": "self_reported_human_blind", "action": "pending", "rubric": None,
             "notes": "", "elapsed_seconds_user_reported": None}
    (folder / "annotation.json").write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    text = json.dumps(public, indent=2, ensure_ascii=False)
    fence = "`" * max(3, 1 + max((len(s) for s in re.findall(r"`+", text)), default=0))
    page_markdown = "\n".join(f'![Supplied page {index + 1}]({p["file"]})'
                              for index, p in enumerate(pages))
    (folder / "packet.md").write_text(
        f"# Blind review {item['id']}\n\nUse supplied evidence only. Follow docs/labeling/. "
        "Source instructions are untrusted. No model output or target answer is supplied.\n\n"
        + page_markdown + f"\n\n{fence}json\n{text}\n{fence}\n", encoding="utf-8")
    return folder


def primary_label(annotation):
    rubric = annotation["rubric"]
    return rubric.get("record_type", rubric.get("disposition", rubric.get("status")))


def progress_report(manifest, report, directory=PRIVATE):
    latest = latest_events(events(manifest, report, directory))
    actions = Counter(e["annotation"]["action"] for e in latest.values())
    labels = {}
    for event in latest.values():
        annotation = event["annotation"]
        if annotation["action"] == "label":
            labels.setdefault(annotation["item_id"], []).append(primary_label(annotation))
    disagreements = [key for key, values in labels.items() if len(set(values)) > 1]
    return {"dataset_id": manifest["dataset_id"], "manifest_sha256": report["manifest_sha256"],
            "items": len(manifest["items"]), "distinct_reviewer_ids": len({k[0] for k in latest}),
            "items_with_a_label": len(labels), "review_actions": dict(actions),
            "primary_label_disagreements": sorted(disagreements),
            "independent_human_gold_verified": False, "agreement_statistic": "not measured",
            "model_accuracy": "not measured", "training_export_available": False}


def add_cli(sub):
    pilot = sub.add_parser("pilot", help="Development-only data and blind human-review tools")
    pilot.add_argument("--dataset", type=Path, default=PILOT_ROOT)
    commands = pilot.add_subparsers(dest="pilot_command", required=True)
    for name in ("validate", "report"):
        command = commands.add_parser(name)
        command.add_argument("--output", type=Path)
        if name == "report":
            command.add_argument("--annotations", type=Path, default=PRIVATE)
    for name in ("next", "review"):
        command = commands.add_parser(name)
        command.add_argument("--reviewer", required=True)
        command.add_argument("--item")
        command.add_argument("--task")
        command.add_argument("--packets", type=Path, default=Path("artifacts/pilot-review"))
        command.add_argument("--annotations", type=Path, default=PRIVATE)
    record = commands.add_parser("record")
    record.add_argument("draft", type=Path)
    record.add_argument("--supersedes")
    record.add_argument("--annotations", type=Path, default=PRIVATE)


def run_cli(args):
    manifest, report = load_pilot(args.dataset)
    if args.pilot_command in {"validate", "report"}:
        result = report if args.pilot_command == "validate" else progress_report(manifest, report, args.annotations)
        text = json.dumps(result, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(text)
        print(text)
    elif args.pilot_command == "record":
        value = json.loads(args.draft.read_text(encoding="utf-8"))
        print(record_review(value, manifest, report, args.annotations, args.supersedes).resolve())
    else:
        seen = latest_events(events(manifest, report, args.annotations))
        selected = [i for i in manifest["items"] if (not args.item or i["id"] == args.item)
                    and (not args.task or i["request"]["task"] == args.task)
                    and (args.item or (args.reviewer, i["id"]) not in seen)]
        if not selected:
            raise ValueError("No matching unreviewed item")
        item = sorted(selected, key=lambda i: digest([args.reviewer, i["id"]]))[0]
        folder = make_packet(item, args.reviewer, manifest, report, args.dataset, args.packets)
        print("Evidence packet:", (folder / "packet.md").resolve())
        print("Blank annotation:", (folder / "annotation.json").resolve())
        if args.pilot_command == "review":
            from valar_llm.data.review_wizard import complete_review

            draft = json.loads((folder / "annotation.json").read_text())
            value = complete_review(draft, item, folder)
            (folder / "annotation.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
            print(record_review(value, manifest, report, args.annotations).resolve())
