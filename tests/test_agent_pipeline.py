"""Unit tests for the code-generation orchestration loop (offline)."""

import pandas as pd

import agent_pipeline


def _df():
    return pd.DataFrame(
        {
            "HADM_ID": [1, 1, 2],
            "FLAG": ["abnormal", "normal", "abnormal"],
            "VALUENUM": [1.0, 2.0, 3.0],
        }
    )


class _Seq:
    """A fake complete_fn returning a fixed sequence of replies (last repeats)."""

    def __init__(self, *replies):
        self.replies = list(replies)
        self.calls = 0

    def __call__(self, system, user, max_tokens=None):
        reply = self.replies[min(self.calls, len(self.replies) - 1)]
        self.calls += 1
        return reply


def test_success_first_attempt():
    out = agent_pipeline.run_codegen(
        "abnormal rows", df=_df(), complete_fn=_Seq("result = df[df['FLAG'] == 'abnormal']")
    )
    assert out["success"]
    assert isinstance(out["result"], pd.DataFrame)
    assert out["correction_applied"] is False
    assert len(out["attempts"]) == 1
    assert out["method"] == "LLM code-gen"


def test_refines_after_runtime_error():
    seq = _Seq("result = undefined_name", "result = df.head(1)")
    out = agent_pipeline.run_codegen("first row", df=_df(), complete_fn=seq)
    assert out["success"]
    assert out["correction_applied"] is True
    assert len(out["attempts"]) == 2


def test_malicious_code_is_blocked_and_fails():
    out = agent_pipeline.run_codegen(
        "leak", df=_df(), complete_fn=_Seq("import os\nresult = os.getcwd()")
    )
    assert not out["success"]
    assert any(a["execution"]["status"] == "Blocked by sandbox" for a in out["attempts"])


def test_empty_question_rejected():
    out = agent_pipeline.run_codegen("   ", df=_df())
    assert not out["success"] and "type a question" in out["status"].lower()


def test_llm_error_degrades_gracefully():
    def boom(system, user, max_tokens=None):
        raise RuntimeError("network down")

    out = agent_pipeline.run_codegen("anything", df=_df(), complete_fn=boom)
    assert not out["success"] and "failed" in out["status"].lower()


def test_max_attempts_respected():
    seq = _Seq("result = df['missing'].sum()")  # KeyError every time
    out = agent_pipeline.run_codegen("bad", df=_df(), complete_fn=seq, max_attempts=2)
    assert not out["success"]
    assert len(out["attempts"]) == 2
