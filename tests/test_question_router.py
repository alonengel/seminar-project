"""Unit tests for the controlled natural-language question router."""

import inspect

import question_router
import questions
from question_router import route_question


def test_abnormal_results_routes_to_q1():
    r = route_question("Show abnormal lab results for admission 145834")
    assert r["matched"] and r["question_id"] == 1
    assert r["params"]["hadm_id"] == 145834


def test_latest_value_routes_to_q2_with_resolved_lab():
    r = route_question("What is the latest chloride value for admission 199884?")
    assert r["matched"] and r["question_id"] == 2
    assert r["params"]["hadm_id"] == 199884
    assert r["params"]["itemid"] == 50902


def test_trend_routes_to_q3():
    r = route_question("Show hematocrit trend for admission 107521")
    assert r["matched"] and r["question_id"] == 3
    assert r["params"]["itemid"] == 51221


def test_compare_first_last_routes_to_q5():
    r = route_question("Compare first and last pO2 values for admission 177047")
    assert r["matched"] and r["question_id"] == 5
    assert r["params"]["itemid"] == 50821


def test_summary_routes_to_q6():
    r = route_question("summary statistics of glucose for admission 145834")
    assert r["matched"] and r["question_id"] == 6


def test_count_abnormal_routes_to_q7():
    r = route_question("count abnormal vs normal results for admission 145834")
    assert r["matched"] and r["question_id"] == 7


def test_all_tests_routes_to_q4():
    r = route_question("show all lab tests for admission 145834")
    assert r["matched"] and r["question_id"] == 4


def test_patient_admissions_routes_to_q11():
    r = route_question("list all admissions for patient 3")
    assert r["matched"] and r["question_id"] == 11
    assert r["params"]["subject_id"] == 3


def test_abnormal_all_admissions_routes_to_q12():
    r = route_question("show me the abnormal lab results for all the admissions")
    assert r["matched"] and r["question_id"] == 12
    assert r["params"] == {}


def test_unrecognized_question_is_rejected():
    r = route_question("what is the weather today")
    assert not r["matched"]


def test_missing_admission_is_rejected_with_hint():
    r = route_question("latest chloride value")
    assert not r["matched"]
    assert "admission" in r["message"].lower()


def test_unknown_admission_is_rejected_clearly():
    # 107522 does not exist (107521 does) - report the real problem, not a lab error.
    r = route_question("Show hematocrit trend for admission 107522")
    assert not r["matched"]
    assert "not found" in r["message"].lower()


def test_unknown_patient_is_rejected_clearly():
    r = route_question("list all admissions for patient 999999")
    assert not r["matched"]
    assert "not found" in r["message"].lower()


def test_empty_input_is_rejected():
    assert not route_question("")["matched"]


def test_routed_params_satisfy_function_signature():
    """Routed params must cover the target data function's arguments."""
    r = route_question("Show hematocrit trend for admission 107521")
    spec = questions.get_question(r["question_id"])
    needed = set(inspect.signature(spec.func).parameters)
    assert needed <= set(r["params"])


def test_build_route_result_rejects_unknown_admission():
    r = question_router.build_route_result(1, hadm_id=999999)
    assert not r["matched"] and "not found" in r["message"].lower()


def test_build_route_result_requires_itemid():
    r = question_router.build_route_result(2, hadm_id=145834, itemid=None)
    assert not r["matched"]


def test_build_route_result_success_sets_method():
    r = question_router.build_route_result(1, hadm_id=145834, method="rules")
    assert r["matched"] and r["question_id"] == 1 and r["method"] == "rules"


def test_build_route_result_aggregate_needs_no_params():
    r = question_router.build_route_result(12)
    assert r["matched"] and r["question_id"] == 12 and r["params"] == {}


def test_smart_route_uses_rules_when_possible():
    r = question_router.smart_route("Show hematocrit trend for admission 107521")
    assert r["matched"] and r["question_id"] == 3 and r.get("method") == "rules"


def test_smart_route_falls_back_to_llm(monkeypatch):
    import llm_router
    monkeypatch.setattr(llm_router, "llm_available", lambda: True)
    fake = {"matched": True, "question_id": 4, "params": {"hadm_id": 145834},
            "lab_label": None, "message": "[4] all tests", "method": "LLM"}
    monkeypatch.setattr(llm_router, "llm_route_question", lambda text: fake)
    r = question_router.smart_route("some phrasing the rules cannot parse zzz")
    assert r["matched"] and r.get("method") == "LLM"


def test_smart_route_returns_rule_failure_when_no_llm(monkeypatch):
    import llm_router
    monkeypatch.setattr(llm_router, "llm_available", lambda: False)
    r = question_router.smart_route("zzz nonsense that matches nothing")
    assert not r["matched"]


def test_smart_route_prefers_llm_failure_reason(monkeypatch):
    import llm_router
    monkeypatch.setattr(llm_router, "llm_available", lambda: True)
    fake = {"matched": False, "question_id": None, "params": {}, "lab_label": None,
            "message": "Could not find a lab test for admission 107521."}
    monkeypatch.setattr(llm_router, "llm_route_question", lambda text: fake)
    r = question_router.smart_route("how did blood counts move during stay 107521")
    assert not r["matched"] and "lab test" in r["message"].lower()


def test_smart_route_keeps_rule_reason_on_llm_error(monkeypatch):
    import llm_router
    monkeypatch.setattr(llm_router, "llm_available", lambda: True)
    fake = {"matched": False, "question_id": None, "params": {}, "lab_label": None,
            "message": "LLM interpretation failed (RuntimeError). Try the dropdown."}
    monkeypatch.setattr(llm_router, "llm_route_question", lambda text: fake)
    r = question_router.smart_route("zzz unparseable nonsense")
    assert not r["matched"] and "recognise" in r["message"].lower()


def test_route_rules_mode():
    r = question_router.route("Show hematocrit trend for admission 107521", mode="rules")
    assert r["matched"] and r["question_id"] == 3 and r.get("method") == "rules"


def test_route_auto_mode_uses_rules_when_possible():
    r = question_router.route("Show hematocrit trend for admission 107521")
    assert r["matched"] and r.get("method") == "rules"


def test_route_llm_mode_without_key_is_rejected(monkeypatch):
    import llm_router
    monkeypatch.setattr(llm_router, "llm_available", lambda: False)
    r = question_router.route("anything", mode="llm")
    assert not r["matched"] and "not configured" in r["message"].lower()


def test_route_llm_mode_with_fake(monkeypatch):
    import llm_router
    monkeypatch.setattr(llm_router, "llm_available", lambda: True)
    fake = {"matched": True, "question_id": 1, "params": {"hadm_id": 145834},
            "lab_label": None, "message": "[1] abnormal", "method": "LLM"}
    monkeypatch.setattr(llm_router, "llm_route_question", lambda text: fake)
    r = question_router.route("abnormal results for 145834", mode="llm")
    assert r["matched"] and r["method"] == "LLM"


def test_route_codegen_mode_delegates(monkeypatch):
    import agent_pipeline
    sentinel = {"success": True, "method": "LLM code-gen", "result": None}
    monkeypatch.setattr(agent_pipeline, "run_codegen", lambda text: sentinel)
    out = question_router.route("compute the mean glucose overall", mode="codegen")
    assert out is sentinel
