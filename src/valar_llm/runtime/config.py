import json
import re
from pathlib import Path


def load_config(path="configs/phase0.json"):
    config = json.loads(Path(path).read_text(encoding="utf-8"))
    if not re.fullmatch(r"[a-f0-9]{40}", config["revision"]):
        raise ValueError("An immutable model/processor commit is required")
    if config["training_steps"] not in range(1, 11):
        raise ValueError("Phase 0 permits only 1..10 training smoke steps")
    for key in ("max_input_tokens", "max_new_tokens", "max_images", "max_image_pixels",
                "processor_max_pixels", "max_request_bytes", "daily_request_limit"):
        if type(config[key]) is not int or config[key] <= 0:
            raise ValueError(f"Invalid positive limit: {key}")
    return config
