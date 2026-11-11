"""Private-caller Gradio smoke service. Run from a prepared ZeroGPU Space root."""
import hashlib
import os
import threading
import time
from pathlib import Path

import gradio as gr
import spaces
from PIL import Image

from valar_llm.contracts.requests import REQUEST
from valar_llm.contracts.validation import validate_output
from valar_llm.gateway.admission import AdmissionError, authenticate, reserve
from valar_llm.runtime.config import load_config
from valar_llm.runtime.model import generate, load_model

CONFIG = load_config()
LOCK = threading.Lock()
MODEL = PROCESSOR = None
ADAPTER_HASH = None


def load_images(paths, request):
    expected = len(getattr(request.payload, "evidence", []))
    if len(paths) != expected or len(paths) > CONFIG["max_images"]:
        raise ValueError("Image/evidence count mismatch")
    images = []
    try:
        for path in paths:
            if Path(path).stat().st_size > 4_000_000:
                raise ValueError("Image exceeds byte budget")
            with Image.open(path) as image:
                if image.width * image.height > CONFIG["max_image_pixels"]:
                    raise ValueError("Image exceeds pixel budget")
                images.append(image.convert("RGB"))
        return images
    except Exception:
        for image in images:
            image.close()
        raise


@spaces.GPU(duration=CONFIG["gpu_duration_seconds"])
def gpu_call(request, images):
    if MODEL is None:
        raise RuntimeError("Model must be prepared on CPU before GPU allocation")
    MODEL.to("cuda")
    try:
        result = generate(MODEL, PROCESSOR, request, images, CONFIG)
        return validate_output(request, result)
    finally:
        MODEL.to("cpu")


def prepare_cpu_model():
    global MODEL, PROCESSOR, ADAPTER_HASH
    if MODEL is None:
        adapter = os.getenv("VALAR_ADAPTER_DIR") or None
        # Download/CPU initialization must not consume the short GPU allocation window.
        MODEL, PROCESSOR = load_model(CONFIG, adapter=adapter, cpu=True)
        if adapter:
            ADAPTER_HASH = hashlib.sha256(
                (Path(adapter) / "valar-manifest.json").read_bytes()
            ).hexdigest()


def predict(api_key, request_json, image_files):
    images = []
    acquired = False
    start = time.perf_counter()
    try:
        authenticate(os.getenv("VALAR_API_KEY", ""), api_key or "")
        if os.getenv("VALAR_ENABLE_GPU") != "1" or not os.getenv("SPACE_ID"):
            raise AdmissionError("disabled")
        if len(request_json.encode("utf-8")) > CONFIG["max_request_bytes"]:
            raise AdmissionError("invalid_request")
        request = REQUEST.validate_json(request_json)
        images = load_images(image_files or [], request)
        acquired = LOCK.acquire(blocking=False)
        if not acquired:
            raise AdmissionError("queue_saturated")
        reserve(Path("artifacts/admission.sqlite"), CONFIG["daily_request_limit"])
        prepare_cpu_model()
        result = gpu_call(request, images)
        return {"status": "ok", "task": request.task, "model_revision": CONFIG["revision"],
                "adapter_manifest_sha256": ADAPTER_HASH,
                "elapsed_seconds": time.perf_counter() - start, "output": result,
                "semantic_support": "unverified"}
    except AdmissionError as exc:
        return {"status": exc.status}
    except (ValueError, TypeError, OSError):
        return {"status": "invalid_input_or_output"}
    except Exception:
        # Do not log raw evidence, credentials, or provider exception payloads.
        return {"status": "provider_failure"}
    finally:
        for image in images:
            image.close()
        if acquired:
            LOCK.release()


def main():
    if len(os.getenv("VALAR_API_KEY", "")) < 32:
        raise RuntimeError("Configure a private VALAR_API_KEY of at least 32 characters")
    demo = gr.Interface(
        fn=predict,
        inputs=[gr.Textbox(label="Application key", type="password"),
                gr.Textbox(label="Versioned task request JSON"),
                gr.File(label="Ordered page images", file_count="multiple", type="filepath",
                        file_types=[".png", ".jpg", ".jpeg"])],
        outputs=gr.JSON(), title="Valar LLM · Phase 0 smoke service",
        description="Limited feasibility endpoint. No production quality claim. Synthetic inputs only.",
        flagging_mode="never",
    )
    demo.queue(max_size=2, default_concurrency_limit=1).launch(
        max_file_size="4mb", show_error=False
    )


if __name__ == "__main__":
    main()
