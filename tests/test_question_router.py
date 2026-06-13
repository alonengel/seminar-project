"""Unit tests for the controlled natural-language question router."""

import inspect

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


def test_unrecognized_question_is_rejected():
    r = route_question("what is the weather today")
    assert not r["matched"]


def test_missing_admission_is_rejected_with_hint():
    r = route_question("latest chloride value")
    assert not r["matched"]
    assert "admission" in r["message"].lower()


def test_empty_input_is_rejected():
    assert not route_question("")["matched"]


def test_routed_params_satisfy_function_signature():
    """Routed params must cover the target data function's arguments."""
    r = route_question("Show hematocrit trend for admission 107521")
    spec = questions.get_question(r["question_id"])
    needed = set(inspect.signature(spec.func).parameters)
    assert needed <= set(r["params"])
