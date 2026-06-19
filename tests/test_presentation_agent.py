"""Unit tests for the presentation agent (rule-based + optional LLM override)."""

import pandas as pd

import presentation_agent as pa


def test_none_for_non_dataframe_or_empty():
    assert pa.suggest_view(5) is None
    assert pa.suggest_view(pd.DataFrame()) is None


def test_none_when_no_numeric_column():
    df = pd.DataFrame({"LABEL": ["a", "b"], "CODE": ["x", "y"]})
    assert pa.suggest_view(df) is None


def test_line_for_timeseries():
    df = pd.DataFrame(
        {"CHARTTIME": pd.to_datetime(["2020-01-01", "2020-01-02"]), "VALUENUM": [1.0, 2.0]}
    )
    spec = pa.suggest_view(df)
    assert spec == {"chart": "line", "x": "CHARTTIME", "y": "VALUENUM"}


def test_bar_for_small_id_breakdown():
    df = pd.DataFrame({"HADM_ID": [1, 2, 3], "Abnormal": [5, 2, 9]})
    spec = pa.suggest_view(df)
    assert spec["chart"] == "bar" and spec["x"] == "HADM_ID" and spec["y"] == "Abnormal"


def test_none_for_large_non_timeseries():
    df = pd.DataFrame({"HADM_ID": range(60), "Abnormal": range(60)})
    assert pa.suggest_view(df) is None


def test_llm_can_override_chart():
    df = pd.DataFrame({"HADM_ID": [1, 2, 3], "Abnormal": [5, 2, 9]})

    def fake(system, user, max_tokens=None):
        return "line"

    spec = pa.suggest_view(df, question="trend?", complete_fn=fake)
    assert spec["chart"] == "line"


def test_llm_can_suppress_chart():
    df = pd.DataFrame({"HADM_ID": [1, 2, 3], "Abnormal": [5, 2, 9]})

    def fake(system, user, max_tokens=None):
        return "none, a table is better"

    assert pa.suggest_view(df, question="list", complete_fn=fake) is None
