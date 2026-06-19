"""Unit tests for the programmer agent (offline; complete_fn injected)."""

import pandas as pd

import code_agent


def _df():
    return pd.DataFrame({"HADM_ID": [1, 2], "VALUENUM": [1.0, 2.0]})


def test_build_schema_lists_columns_and_sample():
    schema, sample = code_agent.build_schema(_df())
    assert "HADM_ID" in schema and "VALUENUM" in schema
    assert isinstance(sample, list) and len(sample) == 2


def test_extract_code_from_fence():
    assert code_agent.extract_code("```python\nresult = 1\n```") == "result = 1"
    assert code_agent.extract_code("```\nresult = 2\n```") == "result = 2"


def test_extract_code_plain():
    assert code_agent.extract_code("result = df.head()") == "result = df.head()"


def test_extract_plan_from_comments():
    code = "# plan: filter abnormal rows\nresult = df[df['FLAG'] == 'abnormal']"
    assert "filter abnormal rows" in code_agent.extract_plan(code)


def test_generate_uses_injected_complete_fn():
    def fake(system, user, max_tokens=None):
        return "```python\nresult = df.head()\n```"

    schema, sample = code_agent.build_schema(_df())
    code = code_agent.generate_analysis_code("show data", schema, sample=sample, complete_fn=fake)
    assert code == "result = df.head()"


def test_generate_includes_feedback_in_prompt():
    captured = {}

    def fake(system, user, max_tokens=None):
        captured["user"] = user
        return "result = 1"

    code_agent.generate_analysis_code(
        "q", "Columns: A (int64)", feedback="NameError: name 'foo' is not defined", complete_fn=fake
    )
    assert "Feedback:" in captured["user"]
    assert "NameError" in captured["user"]
