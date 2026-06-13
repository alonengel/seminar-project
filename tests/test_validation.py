"""Unit tests for the validation module."""

from types import SimpleNamespace

import pandas as pd

from validation import validate_result


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
