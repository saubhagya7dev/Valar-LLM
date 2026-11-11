import hashlib
import json

import pytest

from valar_llm.runtime.output import parse_output


def test_plain_json_retains_strict_validity():
    raw = '{"status":"insufficient","claims":[]}'
    diagnostics = {}
    assert parse_output(raw, diagnostics) == {"status": "insufficient", "claims": []}
    assert diagnostics == {"strict_json_valid": True, "output_normalization": "none",
                           "raw_output_sha256": hashlib.sha256(raw.encode()).hexdigest()}


@pytest.mark.parametrize("fence", ["json", "JSON", ""])
def test_single_whole_response_fence_is_reported_without_repairing_facts(fence):
    # Actual observed bad compact answer: unwrapping must NOT change the wrong category
    # or substitute a supported mechanism for the model's copied instruction text.
    value = {"k": 1, "m": "mechanism preserving negation", "p": "prerequisite or unknown"}
    raw = f"```{fence}\n{json.dumps(value)}\n```"
    diagnostics = {}
    assert parse_output(raw, diagnostics) == value
    assert diagnostics["strict_json_valid"] is False
    assert diagnostics["output_normalization"] == "single_json_fence"


@pytest.mark.parametrize("raw", [
    'Here is the answer: {"k":2}',
    '```json\n{"k":2}\n```\nAdditional explanation.',
    '```json\n{"k":2}\n```\n```json\n{"k":1}\n```',
    '```json\n{"k":2,}\n```',
    '```json\n{"k":2}',
    '<think>reasoning</think>{"k":2}',
    '',
])
def test_arbitrary_prose_truncation_and_invalid_json_remain_failures(raw):
    with pytest.raises(json.JSONDecodeError) as error:
        parse_output(raw)
    assert error.value.doc == raw
