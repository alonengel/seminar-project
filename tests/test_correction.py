"""Unit tests for the rule-based correction loop."""

from types import SimpleNamespace

import pandas as pd

from correction import correct_generated_code, run_with_correction


def test_typo_in_function_name_is_corrected():
    code = "result = get_lates_lab_value(1, 2)"
    out = correct_generated_code(code, {}, {})
    assert "get_latest_lab_value(1, 2)" in out


def test_valid_similar_name_is_not_corrupted():
    # Regression: "get_abnormal_result" is a prefix of this valid name and must
    # not be rewritten into "get_abnormal_resultss_for_lab".
    code = "result = get_abnormal_results_for_lab(145834, 50893)"
    out = correct_generated_code(code, {"message": "empty"}, {"error": None})
    assert "get_abnormal_resultss_for_lab" not in out
    assert "get_abnormal_results_for_lab" in out


def test_run_with_correction_recovers_from_typo():
    def get_latest_lab_value(hadm_id, itemid):
        return pd.DataFrame([{
            "HADM_ID": hadm_id, "ITEMID": itemid, "LABEL": "X",
            "VALUENUM": 1, "VALUEUOM": "u", "CHARTTIME": "2101-01-01",
        }])

    spec = SimpleNamespace(
        id=2,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"],
        extra_validate=lambda df: (len(df) == 1, "expected one row"),
    )

    result = run_with_correction(
        "\nresult = get_lates_lab_value(1, 2)\n",
        {"get_latest_lab_value": get_latest_lab_value},
        spec,
        max_attempts=2,
    )
    assert result["success"]
    assert result["correction_applied"]


def test_run_with_correction_gives_up_when_unfixable():
    spec = SimpleNamespace(id=2, expected_columns=["A"], extra_validate=None)
    result = run_with_correction(
        "\nresult = undefined_function()\n",
        {},
        spec,
        max_attempts=2,
    )
    assert not result["success"]
