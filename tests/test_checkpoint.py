import json
import struct

import pytest

from valar_llm.eval.checkpoint import inspect_tensors


def data(values=(0.125, -0.25), *, start=0, end=8):
    header = json.dumps({"module.lora_B.weight": {"dtype": "F32", "shape": [1, 2],
                                                "data_offsets": [start, end]}}).encode()
    return struct.pack("<Q", len(header)) + header + struct.pack("<2f", *values)


def test_f32_inspection_measures_saved_factors_without_torch():
    result = inspect_tensors(data())
    assert result["all_weights_finite"]
    assert result["parameter_count"] == 2
    assert result["tensors"][0]["nonzero_elements"] == 2


@pytest.mark.parametrize("bad", [b"short", data((float("nan"), 0)), data((float("inf"), 0)),
                                 data(start=1, end=8), data(start=4, end=12), data() + b"extra"])
def test_truncated_nonfinite_and_inconsistent_tensor_data_are_rejected(bad):
    with pytest.raises(ValueError):
        inspect_tensors(bad)
