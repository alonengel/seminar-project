"""Unit tests for the code-generation module."""

import pytest

import questions
from code_generation import generate_code


def test_generate_code_single_argument():
    spec = questions.get_question(1)  # get_abnormal_results(hadm_id)
    code = generate_code(spec, {"hadm_id": 145834})
    assert code.strip() == "result = get_abnormal_results(145834)"


def test_generate_code_two_arguments():
    spec = questions.get_question(2)  # get_latest_lab_value(hadm_id, itemid)
    code = generate_code(spec, {"hadm_id": 145834, "itemid": 50893})
    assert code.strip() == "result = get_latest_lab_value(145834, 50893)"


def test_generate_code_quotes_date_strings():
    spec = questions.get_question(10)  # get_lab_values_in_range(hadm_id, itemid, start_time, end_time)
    code = generate_code(
        spec,
        {"hadm_id": 145834, "itemid": 50893, "start_time": "2101-10-20", "end_time": "2101-10-22"},
    )
    assert "'2101-10-20'" in code and "'2101-10-22'" in code


def test_generate_code_missing_param_raises():
    spec = questions.get_question(2)
    with pytest.raises(KeyError):
        generate_code(spec, {"hadm_id": 145834})  # missing itemid
