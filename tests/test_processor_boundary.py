"""Reproduce the media-scan assumption in the pinned Transformers ProcessorMixin."""
from types import SimpleNamespace

import pytest

from valar_llm.contracts.requests import REQUEST
from valar_llm.data.fixtures import fixture_images, load_cases
from valar_llm.runtime.model import encode
from valar_llm.runtime.prompts import messages_for


class MediaScanningProcessor:
    def apply_chat_template(self, messages, **kwargs):
        self.messages = messages
        self.kwargs = kwargs
        # This is the upstream 4.57.1 behavior that failed on system/assistant strings.
        self.visuals = [content for message in messages for content in message["content"]
                        if content["type"] in ["image", "video"]]
        return {"input_ids": SimpleNamespace(shape=(1, 100))}


@pytest.mark.parametrize("identifier", ["compact-advisory", "review-unknown", "vision-image"])
def test_text_and_image_prompts_survive_processor_media_scan(identifier):
    case = next(c for c in load_cases() if c["id"] == identifier)
    request = REQUEST.validate_python(case["request"])
    images = fixture_images(case)
    try:
        messages = messages_for(request, images)
        original_system = messages[0]["content"]
        processor = MediaScanningProcessor()
        encode(processor, messages, 4096)
        assert processor.messages[0]["content"] == [{"type": "text", "text": original_system}]
        assert messages[0]["content"] == original_system  # Do not mutate prompt provenance.
        assert [v["image"] for v in processor.visuals] == images
    finally:
        for image in images:
            image.close()


def test_training_assistant_text_uses_the_same_boundary_without_generation_prompt():
    processor = MediaScanningProcessor()
    encode(processor, [{"role": "assistant", "content": '{"k":0,"m":"","p":"unknown"}'}],
           4096, generation=False)
    assert processor.messages[0]["content"][0]["type"] == "text"
    assert not processor.kwargs["add_generation_prompt"]


def test_token_budget_still_rejects_instead_of_truncating():
    with pytest.raises(ValueError, match="never truncate image tokens"):
        encode(MediaScanningProcessor(), [{"role": "system", "content": "test"}], 99)
