import json
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator
from jsonschema.exceptions import ValidationError

from .requests import ResearchRequest, ReviewerRequest, VisionRequest

SCHEMAS = {
    "researcher.compact": "compact-incident.v1.json",
    "researcher": "incidents.v1.json",
    "reviewer": "review.v1.json",
    "vision.answer": "grounded-answer.v1.json",
}


def output_schema(task: str) -> dict:
    return json.loads(files("valar_llm.contracts.schemas").joinpath(SCHEMAS[task]).read_text())


def validate_output(request, value: Any) -> dict:
    """Check shape and evidence relationships; this does not prove semantic support."""
    try:
        Draft202012Validator(output_schema(request.task)).validate(value)
    except ValidationError as exc:
        # Do not expose raw model evidence in exception messages/logs.
        raise ValueError("Output does not match the versioned task schema") from exc
    if isinstance(request, ResearchRequest) and request.task == "researcher":
        sources = {s.id: s for s in request.payload.sources}
        ids = [i["id"] for i in value["incidents"]]
        if len(ids) != len(set(ids)):
            raise ValueError("Duplicate incident IDs")
        if len(ids) > 3:
            raise ValueError("Researcher exceeds the three-record application prompt limit")
        for item in value["incidents"]:
            source = sources.get(item["source_id"])
            quote = item["source_quote"]
            if source is None or not 40 <= len(quote) <= 800 or not any(
                quote in p for p in source.passages
            ):
                raise ValueError("Unknown source or noncontiguous/invalid source quote")
    if isinstance(request, VisionRequest):
        supplied = {e.id for e in request.payload.evidence}
        claims = value["claims"]
        if (value["status"] == "insufficient") != (not claims):
            raise ValueError("Insufficient must abstain; factual answers require claims")
        cited = {c for claim in claims for c in claim["citations"]}
        if not cited <= supplied:
            raise ValueError("Unknown evidence ID")
        if value["status"] == "conflicting" and len(cited) < 2:
            raise ValueError("Conflicts require two supplied evidence references")
    if isinstance(request, ReviewerRequest):
        observations = {o.id: o for o in request.payload.profile.observations}
        incidents = {i["id"] for i in request.payload.research.incidents}

        def refs(item):
            if not set(item["evidence_ids"]) <= observations.keys():
                raise ValueError("Unknown repository evidence ID")
            if not set(item.get("incident_ids", [])) <= incidents:
                raise ValueError("Unknown incident ID")

        if len(value["findings"]) > 4 or len(value["followup_requests"]) > 1:
            raise ValueError("Reviewer exceeds bounded finding/follow-up limits")
        if request.payload.followup_answer is not None and value["followup_requests"]:
            raise ValueError("Only one follow-up round is permitted")
        finding_ids = [f["id"] for f in value["findings"]]
        if len(finding_ids) != len(set(finding_ids)):
            raise ValueError("Duplicate finding IDs")
        for finding in value["findings"]:
            refs(finding)
            if not finding["evidence_ids"] or not finding["incident_ids"]:
                raise ValueError("Findings require repository and incident references")
            assessments = finding["prerequisite_assessments"]
            for assessment in assessments:
                refs(assessment)
                if assessment["state"] == "contradicted":
                    raise ValueError("Contradicted material prerequisite must reject the match")
                if assessment["state"] == "supported" and (
                    not assessment["evidence_ids"] or not assessment["incident_ids"]
                    or not any(observations[e].kind == "observed"
                               for e in assessment["evidence_ids"])
                ):
                    raise ValueError("Supported prerequisite requires observed evidence and incident IDs")
            if finding["classification"] == "Supported concern" and (
                not assessments or finding["missing_information"]
                or any(a["state"] != "supported" for a in assessments)
            ):
                raise ValueError("Supported concern requires all prerequisites supported")
            if any(a["state"] == "unknown" for a in assessments) and (
                finding["classification"] != "Needs verification"
            ):
                raise ValueError("Unknown prerequisites require Needs verification")
        for defense in value["existing_defenses"]:
            refs(defense)
        if any(i["incident_id"] not in incidents for i in value["rejected_matches"]):
            raise ValueError("Unknown rejected incident ID")
    return value
