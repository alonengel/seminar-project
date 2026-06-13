"""Unit test for the console result presentation."""

from types import SimpleNamespace

import pandas as pd

from result_presentation import present_result


def test_present_result_prints_key_sections(capsys):
    spec = SimpleNamespace(id=2, label="Return the latest value of a selected lab test")
    final_result = {
        "result": pd.DataFrame([{"HADM_ID": 145834, "VALUENUM": 133}]),
        "execution": {"status": "Execution completed successfully"},
        "validation": {"message": "Validation passed successfully."},
        "correction_applied": False,
        "status": "Execution and validation completed successfully",
    }

    present_result(spec, {"hadm_id": 145834}, "result = get_latest_lab_value(145834, 50893)", final_result)

    out = capsys.readouterr().out
    assert "Return the latest value" in out
    assert "Execution completed successfully" in out
    assert "Validation passed successfully." in out
