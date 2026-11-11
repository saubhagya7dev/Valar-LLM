import json
import sys
import types

import pytest

from valar_llm.eval import smoke


def test_failed_smoke_saves_redacted_diagnostics_and_returns_failure(monkeypatch, tmp_path, capsys):
    output = tmp_path / "attempt.json"
    monkeypatch.setattr(sys, "argv", ["smoke", "--output", str(output), "--case", "compact-advisory"])
    monkeypatch.setenv("VALAR_FREE_ONLINE_RUNTIME", "confirmed")
    torch = types.ModuleType("torch")
    torch.cuda = types.SimpleNamespace(synchronize=lambda: None, get_device_name=lambda: "stub GPU")
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setattr(smoke, "load_model", lambda *a, **kw: (None, None))

    def broken_generation(*args):
        raise TypeError("private source content must not be logged by default")

    monkeypatch.setattr(smoke, "generate", broken_generation)
    with pytest.raises(SystemExit, match="One or more smoke cases failed"):
        smoke.main()
    report = json.loads(output.read_text())
    record = report["records"][0]
    assert not record["contract_valid"]
    assert record["failure_type"] == "TypeError"
    assert record["failure_location"]["function"] == "broken_generation"
    assert "private source content" not in output.read_text()
    assert "private source content" not in capsys.readouterr().err


@pytest.mark.parametrize("debug", [False, True])
def test_unparseable_output_is_preserved_only_for_explicit_synthetic_debug(
    monkeypatch, tmp_path, debug
):
    output = tmp_path / "parse-failure.json"
    argv = ["smoke", "--output", str(output), "--case", "compact-advisory"]
    if debug:
        argv.append("--debug-errors")
    monkeypatch.setattr(sys, "argv", argv)
    monkeypatch.setenv("VALAR_FREE_ONLINE_RUNTIME", "confirmed")
    torch = types.ModuleType("torch")
    torch.cuda = types.SimpleNamespace(synchronize=lambda: None, get_device_name=lambda: "stub GPU")
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setattr(smoke, "load_model", lambda *a, **kw: (None, None))
    raw = '```json\n{"k":2,"m":"test","p":"unknown"}\n```'

    def invalid_json(*args):
        return json.loads(raw)

    monkeypatch.setattr(smoke, "generate", invalid_json)
    with pytest.raises(SystemExit):
        smoke.main()
    record = json.loads(output.read_text())["records"][0]
    assert record["failure_type"] == "JSONDecodeError"
    if debug:
        assert record["raw_output"] == raw  # Preserve exactly; do not silently repair the result.
    else:
        assert "raw_output" not in record
        assert "failure_message" not in record


def test_synthetic_debug_preserves_candidate_rejected_by_evidence_checks(monkeypatch, tmp_path):
    output = tmp_path / "invalid-review.json"
    monkeypatch.setattr(sys, "argv", ["smoke", "--output", str(output), "--case", "review-unknown",
                                     "--debug-errors"])
    monkeypatch.setenv("VALAR_FREE_ONLINE_RUNTIME", "confirmed")
    torch = types.ModuleType("torch")
    torch.cuda = types.SimpleNamespace(synchronize=lambda: None, get_device_name=lambda: "stub GPU")
    monkeypatch.setitem(sys.modules, "torch", torch)
    monkeypatch.setattr(smoke, "load_model", lambda *a, **kw: (None, None))
    candidate = {"summary": "Unsupported model response"}
    monkeypatch.setattr(smoke, "generate", lambda *args: candidate)
    with pytest.raises(SystemExit):
        smoke.main()
    record = json.loads(output.read_text())["records"][0]
    assert not record["contract_valid"]
    assert record["prediction"] == candidate
