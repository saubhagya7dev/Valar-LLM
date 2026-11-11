"""Save actual offline check results; never substitute them for online feasibility evidence."""
import json
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    commands = [
        [sys.executable, "-m", "pytest", "-q"],
        [sys.executable, "-m", "ruff", "check", "."],
        [sys.executable, "-m", "valar_llm.cli", "check"],
    ]
    results = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
        results.append({"command": ["python", *command[1:]], "exit_code": result.returncode,
                        "stdout": result.stdout, "stderr": result.stderr})
    report = {"kind": "offline_verification_only", "created_at": datetime.now(timezone.utc).isoformat(),
              "python": platform.python_version(), "platform": platform.system(),
              "model_executed": False, "gpu_used": False, "cloud_deployed": False,
              "checks": results, "passed": all(r["exit_code"] == 0 for r in results)}
    output = ROOT / "results/phase0/offline-checks.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{'PASS' if report['passed'] else 'FAIL'}: {output}")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
