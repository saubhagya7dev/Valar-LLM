from valar_llm.contracts.requests import REQUEST


def research_request(sources: list[dict], *, compact: bool = False):
    # Pass already-selected source views; retrieval and compact expansion stay upstream.
    return REQUEST.validate_python({
        "task": "researcher.compact" if compact else "researcher",
        "payload": {"sources": sources},
    })


def review_request(profile_view: dict, research_view: dict, followup_answer=None):
    return REQUEST.validate_python({
        "task": "reviewer",
        "payload": {"profile": profile_view, "research": research_view,
                    "followup_answer": followup_answer},
    })
