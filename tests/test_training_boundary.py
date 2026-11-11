import pytest

from valar_llm.train.smoke import answer_boundary


def test_answer_boundary_preserves_full_image_prompt_prefix():
    # Stand-in image token IDs must remain part of the masked prefix.
    prompt = [1, 400, 401, 401, 402, 9]
    assert answer_boundary(prompt + [20, 21, 2], prompt) == len(prompt)


@pytest.mark.parametrize("full,prompt", [
    ([1, 2], [1, 2]),
    ([1, 2], [1, 2, 3]),
    ([1, 99, 3], [1, 2]),
    ([1, 2], []),
])
def test_masking_rejects_empty_answer_and_mismatched_template(full, prompt):
    with pytest.raises(ValueError, match="prefix mismatch or no answer tokens"):
        answer_boundary(full, prompt)
