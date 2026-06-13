"""Unit tests for the question registry."""

import inspect

import pytest

import questions


def test_registry_has_eleven_questions():
    assert len(questions.QUESTION_REGISTRY) == 11


def test_question_ids_are_unique_and_sequential():
    ids = [q.id for q in questions.QUESTION_REGISTRY]
    assert ids == list(range(1, 12))


def test_get_question_returns_spec():
    assert questions.get_question(2).func.__name__ == "get_latest_lab_value"


def test_get_question_invalid_raises():
    with pytest.raises(ValueError):
        questions.get_question(999)


def test_get_question_by_label_roundtrip():
    spec = questions.QUESTION_REGISTRY[0]
    assert questions.get_question_by_label(spec.label) is spec


def test_get_question_by_label_invalid_raises():
    with pytest.raises(ValueError):
        questions.get_question_by_label("not a real question")


def test_build_context_maps_function_names():
    context = questions.build_context()
    for spec in questions.QUESTION_REGISTRY:
        assert spec.func.__name__ in context
        assert callable(context[spec.func.__name__])


def test_every_spec_has_expected_columns():
    for spec in questions.QUESTION_REGISTRY:
        assert spec.expected_columns, f"Q{spec.id} has no expected_columns"


def test_param_defs_cover_all_used_params():
    used = {p for spec in questions.QUESTION_REGISTRY for p in spec.params}
    assert used <= set(questions.PARAM_DEFS), "a question uses an undeclared param widget"


def test_function_args_are_fillable_from_declared_params():
    """Each data function's arguments must be produced by the question's widgets."""
    for spec in questions.QUESTION_REGISTRY:
        fillable = set()
        for widget in spec.params:
            fillable.update(questions.PARAM_DEFS[widget]["fills"])
        func_args = set(inspect.signature(spec.func).parameters)
        assert func_args <= fillable, f"Q{spec.id}: args {func_args - fillable} not fillable"
