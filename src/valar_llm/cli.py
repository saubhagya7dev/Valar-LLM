import argparse
import json
from pathlib import Path

from pydantic import ValidationError

from valar_llm.contracts.requests import REQUEST
from valar_llm.contracts.validation import output_schema
from valar_llm.data.review import add_cli, run_cli
from valar_llm.eval.phase0 import check_fixtures
from valar_llm.runtime.config import load_config


def main():
    parser = argparse.ArgumentParser(prog="valar")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("check")
    sub.add_parser("status")
    schema = sub.add_parser("schemas")
    schema.add_argument("--output", default="schemas")
    add_cli(sub)
    args = parser.parse_args()
    if args.command == "check":
        load_config()
        print(json.dumps(check_fixtures(), indent=2))
    elif args.command == "status":
        print(Path("docs/phase-0.md").read_text(encoding="utf-8"))
    elif args.command == "pilot":
        try:
            run_cli(args)
        except ValidationError as exc:
            fields = [".".join(map(str, error["loc"])) + " (" + error["type"] + ")"
                      for error in exc.errors(include_input=False, include_url=False)]
            parser.exit(2, "Invalid pilot/review fields: " + "; ".join(fields) + "\n")
        except (ValueError, OSError) as exc:
            parser.exit(2, f"Pilot operation rejected: {exc}\n")
        except (KeyboardInterrupt, EOFError):
            parser.exit(130, "Review interrupted. Packet retained; check the review report before resuming.\n")
    else:
        from valar_llm.data.pilot import PilotManifest
        from valar_llm.data.review import ReviewDraft

        target = Path(args.output)
        target.mkdir(parents=True, exist_ok=True)
        (target / "requests.v1.json").write_text(
            json.dumps(REQUEST.json_schema(), indent=2) + "\n", encoding="utf-8"
        )
        for task in ("researcher.compact", "researcher", "reviewer", "vision.answer"):
            (target / f"{task}.response.v1.json").write_text(
                json.dumps(output_schema(task), indent=2) + "\n", encoding="utf-8"
            )
        for name, model in (("pilot-manifest.v1.json", PilotManifest),
                            ("pilot-annotation.v1.json", ReviewDraft)):
            (target / name).write_text(json.dumps(model.model_json_schema(), indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
