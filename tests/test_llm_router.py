"""Unit tests for the optional LLM-assisted router (no real network calls)."""

import pytest

import questions
from llm_router import _catalog, _extract_json, _to_int, llm_route_question


def _fake(json_text):
    """A fake complete_fn that returns a fixed LLM reply string."""
    return lambda system, user: json_text


def test_catalog_lists_all_questions():
    catalog = _catalog()
    assert catalog.count("\n") == len(questions.QUESTION_REGISTRY) - 1
    assert catalog.startswith("1:")


def test_extract_json_variants():
    assert _extract_json('{"a": 1}') == '{"a": 1}'
    assert _extract_json('sure: {"a": 1} done') == '{"a": 1}'
    with pytest.raises(ValueError):
        _extract_json("no json here")


def test_to_int():
    assert _to_int("145834") == 145834
    assert _to_int(145834) == 145834
    assert _to_int(None) is None
    assert _to_int("abc") is None


def test_llm_route_trend_resolves_lab():
    fake = _fake(
        '{"question_id": 3, "hadm_id": 107521, "lab": "hematocrit", '
        '"subject_id": null, "start_time": null, "end_time": null}'
    )
    result = llm_route_question("hematocrit trend for admission 107521", complete_fn=fake)
    assert result["matched"]
    assert result["question_id"] == 3
    assert result["params"]["itemid"] == 51221
    assert result["method"] == "LLM"


def test_llm_route_hadm_only_question():
    fake = _fake('{"question_id": 1, "hadm_id": 145834}')
    result = llm_route_question("abnormal results for 145834", complete_fn=fake)
    assert result["matched"]
    assert result["question_id"] == 1


def test_llm_route_aggregate_question_needs_no_params():
    """'abnormal results for all admissions' -> Q12, which takes no parameters."""
    fake = _fake('{"question_id": 12, "hadm_id": null, "lab": null, "subject_id": null}')
    result = llm_route_question("show me the abnormal lab results for all the admissions", complete_fn=fake)
    assert result["matched"]
    assert result["question_id"] == 12
    assert result["params"] == {}


def test_llm_route_unknown_admission_rejected():
    fake = _fake('{"question_id": 3, "hadm_id": 999999, "lab": "hematocrit"}')
    result = llm_route_question("trend for 999999", complete_fn=fake)
    assert not result["matched"]
    assert "not found" in result["message"].lower()


def test_llm_route_declines_when_no_template_fits():
    """question_id 0 means the model judged no template fits -> reject + point to Advanced."""
    result = llm_route_question(
        "last 10 abnormal results across the whole database",
        complete_fn=_fake('{"question_id": 0, "hadm_id": null}'),
    )
    assert not result["matched"]
    assert "advanced" in result["message"].lower()


def test_llm_route_malformed_response_degrades():
    result = llm_route_question("anything", complete_fn=_fake("sorry, I cannot help"))
    assert not result["matched"]


def test_llm_available_reflects_client(monkeypatch):
    import llm_client
    import llm_router

    monkeypatch.setattr(llm_client, "active_provider", lambda: "openai")
    assert llm_router.llm_available() is True
    monkeypatch.setattr(llm_client, "active_provider", lambda: None)
    assert llm_router.llm_available() is False
