"""Regression coverage for Colab kernels that do not run Python 3.12."""
import json
import sys
import types
from pathlib import Path


def test_setup_provisions_its_own_python_before_installing_gpu_packages(monkeypatch):
    notebook = json.loads(Path("notebooks/phase0_colab.ipynb").read_text(encoding="utf-8"))
    code_cells = ["".join(c["source"]) for c in notebook["cells"] if c["cell_type"] == "code"]
    # The upload cell must allow the actual non-3.12 host that caused the user's failure.
    assert "assert sys.version_info" not in code_cells[0]
    calls = []
    process = types.ModuleType("subprocess")
    process.run = lambda command, **kwargs: calls.append((command, kwargs))
    monkeypatch.setitem(sys.modules, "subprocess", process)
    monkeypatch.setenv("VALAR_FREE_ONLINE_RUNTIME", "")
    exec(compile(code_cells[1], "colab-setup", "exec"), {"sys": sys})
    commands = [command for command, _ in calls]
    install_python = next(i for i, c in enumerate(commands) if "3.12.12" in c)
    gpu_install = next(i for i, c in enumerate(commands) if "requirements/gpu.lock" in c)
    assert install_python < gpu_install
    assert any(c[-4:] == ["venv", "--python", "3.12.12", "/content/valar-env"] for c in commands)
    for command in commands[gpu_install:]:
        if "pip" in command:
            assert command[command.index("--python") + 1] == "/content/valar-env/bin/python"
        else:
            assert command[0] == "/content/valar-env/bin/python"
    assert all(kwargs["check"] for _, kwargs in calls)
