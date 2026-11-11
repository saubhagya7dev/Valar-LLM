import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def load_cases(path="tests/fixtures/cases.json"):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fixture_images(case):
    """Render first-party synthetic page facts, without exposing labels in the prompt text."""
    images = []
    for lines in case.get("page_lines", []):
        image = Image.new("RGB", (640, 320), "white")
        draw = ImageDraw.Draw(image)
        font = ImageFont.load_default(size=24)
        for n, line in enumerate(lines):
            draw.text((28, 32 + 48 * n), line, fill="black", font=font)
        images.append(image)
    return images
