"""Unit tests for the code-generation sandbox (AST allowlist + restricted exec)."""

import pandas as pd

import sandbox


def _df():
    return pd.DataFrame(
        {
            "HADM_ID": [1, 1, 2, 2],
            "FLAG": ["abnormal", "normal", "abnormal", "abnormal"],
            "VALUENUM": [1.0, 2.0, 3.0, 4.0],
        }
    )


# --- check_code: allowed ---
def test_allows_safe_pandas():
    ok, _ = sandbox.check_code("result = df[df['FLAG'] == 'abnormal'].head(5)")
    assert ok


def test_allows_groupby_and_arithmetic():
    ok, _ = sandbox.check_code("result = df.groupby('HADM_ID').size().reset_index(name='n')")
    assert ok
    ok2, _ = sandbox.check_code("result = (df['VALUENUM'] * 2 + 1).max()")
    assert ok2


# --- check_code: blocked ---
def test_blocks_import():
    ok, reason = sandbox.check_code("import os\nresult = 1")
    assert not ok and "import" in reason.lower()


def test_blocks_from_import():
    ok, reason = sandbox.check_code("from os import system\nresult = 1")
    assert not ok and "import" in reason.lower()


def test_blocks_open_name():
    ok, reason = sandbox.check_code("result = open('secret.txt').read()")
    assert not ok and "open" in reason.lower()


def test_blocks_dunder_attribute():
    ok, reason = sandbox.check_code("result = df.__class__.__bases__")
    assert not ok and ("private" in reason.lower() or "dunder" in reason.lower())


def test_blocks_dunder_name():
    ok, reason = sandbox.check_code("result = __import__('os')")
    assert not ok and "dunder" in reason.lower()


def test_blocks_file_io_method():
    ok, reason = sandbox.check_code("result = df.to_csv('leak.csv')")
    assert not ok and "to_csv" in reason


def test_blocks_query_engine():
    ok, reason = sandbox.check_code("result = df.query('VALUENUM > 1')")
    assert not ok and "query" in reason


def test_blocks_while_loop():
    ok, reason = sandbox.check_code("while True:\n    result = 1")
    assert not ok and "While" in reason


def test_blocks_function_def():
    ok, reason = sandbox.check_code("def f():\n    return 1\nresult = f()")
    assert not ok


def test_reports_syntax_error():
    ok, reason = sandbox.check_code("result = (")
    assert not ok and "syntax" in reason.lower()


def test_rejects_empty():
    ok, _ = sandbox.check_code("   ")
    assert not ok


# --- run_sandboxed ---
def test_run_success_returns_dataframe():
    out = sandbox.run_sandboxed("result = df[df['FLAG'] == 'abnormal']", _df())
    assert out["success"]
    assert isinstance(out["result"], pd.DataFrame)
    assert (out["result"]["FLAG"] == "abnormal").all()


def test_run_blocked_reports_sandbox():
    out = sandbox.run_sandboxed("import os\nresult = 1", _df())
    assert not out["success"] and out["status"] == "Blocked by sandbox"


def test_run_runtime_error_is_captured():
    out = sandbox.run_sandboxed("result = df['missing_column'].sum()", _df())
    assert not out["success"] and out["status"] == "Execution failed"
    assert "KeyError" in out["error"]


def test_run_caps_rows():
    out = sandbox.run_sandboxed("result = df", _df(), max_rows=2)
    assert out["success"] and len(out["result"]) == 2


def test_run_timeout():
    out = sandbox.run_sandboxed("result = sum(i for i in range(20000000))", _df(), timeout=0.001)
    assert not out["success"] and out["status"] == "Timeout"


def test_safe_builtins_exclude_dangerous():
    for name in ("open", "eval", "exec", "__import__", "getattr"):
        assert name not in sandbox.SAFE_BUILTINS
