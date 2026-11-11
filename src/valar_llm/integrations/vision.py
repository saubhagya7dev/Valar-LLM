from valar_llm.contracts.requests import REQUEST


def grounded_request(query: str, evidence: list[dict], images: list):
    """Preserve version/page IDs and positional image association; never silently zip."""
    if len(evidence) != len(images):
        raise ValueError("Each evidence entry requires exactly one page image")
    return REQUEST.validate_python({"task": "vision.answer", "payload": {
        "query": query, "evidence": evidence,
    }})
