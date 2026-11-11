"""Explicit, read-only upstream snapshot refresh; review generated diffs before accepting."""
import argparse
import hashlib
import json
import runpy
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("upstream", type=Path)
    args = parser.parse_args()
    source = args.upstream / "devsecops" / "contracts.py"
    # This explicit maintenance tool executes the inspected local contract-definition module.
    contracts = runpy.run_path(str(source))
    output = Path("src/valar_llm/contracts/schemas")
    mapping = {"compact-incident": "COMPACT_INCIDENT", "incidents": "INCIDENTS", "review": "REVIEW"}
    for name, key in mapping.items():
        schema = {"$schema": "https://json-schema.org/draft/2020-12/schema",
                  "title": key, **contracts[key]}
        (output / f"{name}.v1.json").write_text(json.dumps(schema, indent=2) + "\n")
    (output / "provenance.json").write_text(json.dumps({
        "captured_on": "2026-11-11", "source": "DevSecOps/devsecops/contracts.py",
        "sha256": hashlib.sha256(source.read_bytes()).hexdigest(), "symbols": mapping,
        "note": "Output wire contracts copied without renaming fields. No upstream changes.",
    }, indent=2) + "\n")


if __name__ == "__main__":
    main()
