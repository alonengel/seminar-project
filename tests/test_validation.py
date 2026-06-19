"""Unit tests for the validation module."""

from types import SimpleNamespace

import pandas as pd

from validation import validate_freeform_result, validate_result


def _spec(expected_columns, extra_validate=None):
    return SimpleNamespace(expected_columns=expected_columns, extra_validate=extra_validate)


def _exec_ok(result):
    return {"success": True, "result": result, "error": None}


def test_valid_dataframe_passes():
    df = pd.DataFrame([{"A": 1, "B": 2}])
    out = validate_result(_spec(["A", "B"]), _exec_ok(df))
    assert out["valid"]


def test_execution_failure_fails():
    out = validate_result(_spec(["A"]), {"success": False, "error": "boom", "result": None})
    assert not out["valid"]


def test_none_result_fails():
    out = validate_result(_spec(["A"]), _exec_ok(None))
    assert not out["valid"]


def test_non_dataframe_fails():
    out = validate_result(_spec(["A"]), _exec_ok(123))
    assert not out["valid"]


def test_missing_columns_fails():
    df = pd.DataFrame([{"A": 1}])
    out = validate_result(_spec(["A", "B"]), _exec_ok(df))
    assert not out["valid"]
    assert "B" in out["details"]


def test_empty_dataframe_fails():
    df = pd.DataFrame(columns=["A"])
    out = validate_result(_spec(["A"]), _exec_ok(df))
    assert not out["valid"]


def test_extra_validate_can_fail():
    df = pd.DataFrame([{"A": 1}, {"A": 2}])
    spec = _spec(["A"], extra_validate=lambda d: (len(d) == 1, "need exactly one"))
    out = validate_result(spec, _exec_ok(df))
    assert not out["valid"]
    assert out["message"] == "need exactly one"


def test_string_result_is_valid():
    out = validate_result(_spec(["A"]), _exec_ok("some text"))
    assert out["valid"]


# --- freeform validator (LLM code-gen path) ---
def test_freeform_dataframe_passes():
    out = validate_freeform_result(pd.DataFrame([{"A": 1}]))
    assert out["valid"]


def test_freeform_empty_dataframe_is_valid_no_records():
    out = validate_freeform_result(pd.DataFrame(columns=["A"]))
    assert out["valid"] and out["details"] == "empty"


def test_freeform_series_and_scalar_pass():
    assert validate_freeform_result(pd.Series([1, 2, 3]))["valid"]
    assert validate_freeform_result(42)["valid"]
    assert validate_freeform_result("text")["valid"]


def test_freeform_none_fails():
    assert not validate_freeform_result(None)["valid"]


def test_freeform_unsupported_type_fails():
    out = validate_freeform_result({"a": 1})
    assert not out["valid"]


def test_freeform_truncation_note():
    out = validate_freeform_result(pd.DataFrame({"A": range(10)}), max_rows=10)
    assert out["valid"] and "first 10" in out["message"]
