"""Terminal-only labeling: user choices have no selected/default model answer."""
import json


def choose(prompt, options):
    print(prompt)
    for index, value in enumerate(options, 1):
        print(f"  {index}. {value}")
    while True:
        answer = input("Select a number (no default): ").strip()
        if answer.isdigit() and 1 <= int(answer) <= len(options):
            return options[int(answer) - 1]
        print("Choose one of the displayed numbers.")


def entries(prompt):
    print(prompt + " Enter one item per line; blank line ends the list.")
    result = []
    while value := input("> ").strip():
        result.append(value)
    return result


def ids(prompt):
    return [s.strip() for s in input(prompt + " (comma-separated supplied IDs, blank for none): ").split(",") if s.strip()]


def complete_review(draft, item, folder):
    print("Read the packet and original page images first. No model output is supplied.")
    print(json.dumps(item["request"], indent=2))
    for page in sorted(folder.glob("page-*.png")):
        print("Open page image:", page.resolve())
    action = choose("Your review action:", ["label", "skip", "needs_adjudication"])
    draft["action"] = action
    if action != "label":
        draft["notes"] = input("Reason (required): ").strip()
        return draft
    task = item["request"]["task"]
    if task.startswith("researcher"):
        record_type = choose("What does the supplied source establish?", [
            "observed_attack", "vulnerability_advisory", "background_guidance", "insufficient_evidence"])
        mechanism = input("Evidence-supported mechanism, preserving negation (blank when insufficient): ").strip()
        prerequisites = entries("Documented prerequisites; do not guess")
        quotes = []
        while source_id := input("Supporting quote source ID (blank ends quotes): ").strip():
            quotes.append({"source_id": source_id, "quote": input("Paste exact contiguous quote (40-800 chars): ")})
        rubric = {"role": "researcher", "record_type": record_type, "mechanism": mechanism,
                  "prerequisites": prerequisites, "supporting_quotes": quotes,
                  "unknowns": entries("Unsupported/missing facts")}
    elif task == "reviewer":
        disposition = choose("Overall disposition:", ["supported_concern", "needs_verification",
                              "background_lesson", "reject_match", "insufficient_context"])
        assessments = []
        while prerequisite := input("Material prerequisite (blank ends assessments): ").strip():
            assessments.append({"prerequisite": prerequisite,
                "state": choose("Prerequisite state:", ["supported", "contradicted", "unknown"]),
                "evidence_ids": ids("Repository evidence"), "incident_ids": ids("Incident references"),
                "reason": input("Reason tied to those references: ").strip()})
        defenses = []
        while description := input("Observed existing defense (blank ends defenses): ").strip():
            defenses.append({"description": description, "evidence_ids": ids("Defense evidence")})
        rubric = {"role": "reviewer", "disposition": disposition,
                  "prerequisite_assessments": assessments, "existing_defenses": defenses,
                  "evidence_ids": ids("Overall repository evidence"), "incident_ids": ids("Overall incident references"),
                  "missing_information": entries("Missing facts"), "reason": input("Overall reason: ").strip()}
    else:
        status = choose("Answer status:", ["supported", "insufficient", "conflicting"])
        claims = []
        while text := input("Supported claim (blank ends claims; none when insufficient): ").strip():
            claims.append({"text": text, "citations": ids("Supplied page evidence")})
        rubric = {"role": "vision", "status": status, "claims": claims}
    draft["rubric"] = rubric
    draft["notes"] = input("Optional ambiguity/quality notes: ").strip()
    # Preserve the user's work before validation; no completion is inferred on invalid input.
    (folder / "annotation.json").write_text(json.dumps(draft, indent=2) + "\n", encoding="utf-8")
    return draft
