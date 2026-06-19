"""
Presentation agent: suggest how to visualise a code-generation result.

Rule-based by default (works offline): a DataFrame with a time-like column and a
numeric column suggests a line chart; a small DataFrame with a categorical/id
column and a numeric column suggests a bar chart. Returns a spec dict such as
{"chart": "line", "x": ..., "y": ...} or None when nothing sensible applies.

An LLM can optionally refine the chart choice when a `complete_fn` is provided,
but it is never required - this keeps the feature available offline and in tests.
"""

import pandas as pd

_MAX_BAR_ROWS = 50


def _is_timelike(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return True
    name = str(series.name).lower()
    return "time" in name or "date" in name


def _rule_based_spec(result, numeric_cols):
    time_cols = [c for c in result.columns if _is_timelike(result[c])]
    if time_cols:
        y = next((c for c in numeric_cols if c not in time_cols), numeric_cols[0])
        return {"chart": "line", "x": time_cols[0], "y": y}

    if len(result) <= _MAX_BAR_ROWS:
        non_numeric = [c for c in result.columns if c not in numeric_cols]
        x = non_numeric[0] if non_numeric else result.columns[0]
        if x == numeric_cols[0] and len(numeric_cols) > 1:
            y = numeric_cols[1]
        else:
            y = numeric_cols[0]
        return {"chart": "bar", "x": x, "y": y}

    return None


def _ask_llm_chart(question, columns, complete_fn):
    system = "You pick the best chart for a small result table. Reply with ONE word: line, bar, or none."
    user = f"Question: {question}\nColumns: {columns}\nWhich chart?"
    try:
        resp = complete_fn(system, user, max_tokens=5)
        text = (resp.text if hasattr(resp, "text") else str(resp)).strip().lower()
    except Exception:  # noqa: BLE001 - visualisation is best-effort; fall back to rules
        return None
    for token in ("line", "bar", "none"):
        if token in text:
            return token
    return None


def suggest_view(result, question=None, complete_fn=None):
    """Return a chart spec dict for a DataFrame result, or None if not chartable."""
    if not isinstance(result, pd.DataFrame) or result.empty:
        return None

    numeric_cols = [c for c in result.columns if pd.api.types.is_numeric_dtype(result[c])]
    if not numeric_cols:
        return None

    spec = _rule_based_spec(result, numeric_cols)
    if spec is None:
        return None

    if complete_fn is not None:
        choice = _ask_llm_chart(question, list(result.columns), complete_fn)
        if choice == "none":
            return None
        if choice in ("line", "bar"):
            spec["chart"] = choice

    return spec
