import argparse
import json
from pathlib import Path

from valar_llm.contracts.requests import REQUEST
from valar_llm.contracts.validation import output_schema
from valar_llm.eval.phase0 import check_fixtures
from valar_llm.runtime.config import load_config


def main():
    parser = argparse.ArgumentParser(prog="valar")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("status")
    schema = sub.add_parser("schemas")
    schema.add_argument("--output", default="schemas")
    args = parser.parse_args()
    if args.command == "check":
        load_config()
        print(json.dumps(check_fixtures(), indent=2))
    elif args.command == "status":
        print(Path("docs/phase-0.md").read_text(encoding="utf-8"))
    else:
        target = Path(args.output)
        target.mkdir(parents=True, exist_ok=True)
        (target / "requests.v1.json").write_text(
            json.dumps(REQUEST.json_schema(), indent=2) + "\n", encoding="utf-8"
        )
        for task in ("researcher.compact", "researcher", "reviewer", "vision.answer"):
            (target / f"{task}.response.v1.json").write_text(
                json.dumps(output_schema(task), indent=2) + "\n", encoding="utf-8"
            )


if __name__ == "__main__":
    main()
