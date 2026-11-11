"""Bounded formatting normalization; never repair facts, fields, or invalid JSON."""
import hashlib
import json
import re
from typing import Any


def parse_output(text: str, diagnostics: dict | None = None) -> Any:
    metadata = diagnostics if diagnostics is not None else {}
    metadata.update(strict_json_valid=False, output_normalization="none",
                    raw_output_sha256=hashlib.sha256(text.encode("utf-8")).hexdigest())
    try:
        value = json.loads(text)
    except json.JSONDecodeError as original:
        # Only one whole-response fence is permitted. Do not extract arbitrary
        # objects from prose, remove reasoning, or accept multiple JSON blocks.
        match = re.fullmatch(r"\s*```(?:json)?[ \t]*\r?\n(.*?)\r?\n```\s*", text,
                             flags=re.DOTALL | re.IGNORECASE)
        if match is None:
            raise
        try:
            value = json.loads(match.group(1))
        except json.JSONDecodeError:
            # Keep the original complete text available to synthetic debug capture.
            raise original
        metadata["output_normalization"] = "single_json_fence"
        return value
    metadata["strict_json_valid"] = True
    return value
