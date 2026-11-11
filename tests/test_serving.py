"""Exercise CPU admission and file boundaries without importing a GPU framework."""
import importlib
import json
import sys
import types

import pytest

from valar_llm.contracts.requests import REQUEST
from valar_llm.data.fixtures import load_cases


@pytest.fixture
def service(monkeypatch):
    monkeypatch.setitem(sys.modules, "gradio", types.ModuleType("gradio"))
    spaces = types.ModuleType("spaces")
    spaces.GPU = lambda **kwargs: lambda fn: fn
    monkeypatch.setitem(sys.modules, "spaces", spaces)
    name = "valar_llm.serve.zerogpu"
    sys.modules.pop(name, None)
    service = importlib.import_module(name)
    monkeypatch.setenv("VALAR_API_KEY", "x" * 32)
    monkeypatch.setenv("SPACE_ID", "synthetic/smoke")
    monkeypatch.setenv("VALAR_ENABLE_GPU", "1")

    def unexpected_gpu(*args):
        pytest.fail("Invalid or unauthorized request reached GPU execution")

    monkeypatch.setattr(service, "gpu_call", unexpected_gpu)
    yield service
    sys.modules.pop(name, None)


def compact_request():
    return next(c["request"] for c in load_cases() if c["id"] == "compact-advisory")


def test_unauthorized_and_disabled_never_allocate_gpu(service, monkeypatch):
    raw = json.dumps(compact_request())
    assert service.predict("wrong", raw, []) == {"status": "unauthorized"}
    monkeypatch.setenv("VALAR_ENABLE_GPU", "0")
    assert service.predict("x" * 32, raw, []) == {"status": "disabled"}


def test_invalid_request_and_saturated_worker_never_allocate_gpu(service):
    assert service.predict("x" * 32, "not JSON", []) == {"status": "invalid_input_or_output"}
    service.LOCK.acquire()
    try:
        assert service.predict("x" * 32, json.dumps(compact_request()), []) == {
            "status": "queue_saturated"
        }
    finally:
        service.LOCK.release()


def test_extra_image_rejected_before_opening_local_path(service):
    request = REQUEST.validate_python(compact_request())
    with pytest.raises(ValueError, match="count mismatch"):
        service.load_images(["C:/private/document.png"], request)


def test_image_pixel_limit_checked_before_conversion(service, tmp_path):
    from PIL import Image

    path = tmp_path / "oversized.png"
    Image.new("RGB", (1025, 1025)).save(path)
    request = REQUEST.validate_python(next(c["request"] for c in load_cases()
                                           if c["id"] == "vision-image"))
    with pytest.raises(ValueError, match="pixel budget"):
        service.load_images([path], request)
