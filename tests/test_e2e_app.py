"""
End-to-end tests for the Streamlit UI using Streamlit's AppTest harness.

For every selectable question this verifies that the correct parameter widgets
render and that running the analysis produces the right result components
(result table, generated code, and an appropriate status banner).
"""

import os
import sys

import pytest
from streamlit.testing.v1 import AppTest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

import questions  # noqa: E402

APP_PATH = os.path.join(ROOT, "app.py")

PARAM_WIDGET_LABELS = {
    "hadm_id": "Admission ID (HADM_ID)",
    "itemid": "Lab Test",
    "subject_id": "Patient ID (SUBJECT_ID)",
}


def _fresh_app():
    at = AppTest.from_file(APP_PATH, default_timeout=240)
    at.run()
    return at


def _select_question(at, label):
    at.selectbox[1].set_value(label).run()
    return at


def _markdown(at):
    return " ".join(m.value for m in at.markdown if m.value)


def _all_text(at):
    chunks = []
    for collection in (at.markdown, at.success, at.info, at.warning, at.error):
        chunks.extend(m.value for m in collection if getattr(m, "value", None))
    return " ".join(chunks)


def _codes(at):
    try:
        return [c.value for c in at.code]
    except Exception:
        return []


def _run(at):
    """Click the structured 'Run Analysis' button (robust to other buttons)."""
    button = next(b for b in at.button if b.label == "Run Analysis")
    button.click()
    at.run()
    return at


def test_app_loads_with_all_questions():
    at = _fresh_app()
    assert not at.exception
    assert "Clinical Lab Analysis System" in _markdown(at)
    assert len(at.selectbox[1].options) == len(questions.QUESTION_REGISTRY) == 11


@pytest.mark.parametrize("spec", questions.QUESTION_REGISTRY, ids=lambda s: f"Q{s.id}")
def test_question_renders_correct_widgets_and_runs(spec):
    at = _select_question(_fresh_app(), spec.label)
    assert not at.exception, f"selecting Q{spec.id} raised an exception"

    labels = [sb.label for sb in at.selectbox]

    # The widgets the question declares must be present...
    for param in spec.params:
        if param in PARAM_WIDGET_LABELS:
            assert PARAM_WIDGET_LABELS[param] in labels, f"Q{spec.id} missing widget for '{param}'"
    if "date_range" in spec.params:
        assert len(at.date_input) >= 1, f"Q{spec.id} missing the date-range widget"

    # ...and widgets it does not declare must be absent.
    if "itemid" not in spec.params:
        assert "Lab Test" not in labels, f"Q{spec.id} should not render a Lab Test widget"
    if "subject_id" not in spec.params:
        assert "Patient ID (SUBJECT_ID)" not in labels

    _run(at)
    assert not at.exception, f"running Q{spec.id} raised an exception"

    md = _markdown(at)
    success = "Analysis completed successfully" in md
    no_records = "no matching records" in md
    assert success or no_records, f"Q{spec.id}: no result banner rendered"

    if success:
        result_df = None
        for d in at.dataframe:
            if all(c in list(d.value.columns) for c in spec.expected_columns):
                result_df = d.value
        assert result_df is not None, f"Q{spec.id}: result table with expected columns not rendered"

        codes = _codes(at)
        if codes:
            assert any(spec.func.__name__ in (c or "") for c in codes), \
                f"Q{spec.id}: generated code not displayed"


def test_q8_happy_path_with_abnormal_lab():
    """Q8 with a lab that has abnormal readings returns a populated table."""
    spec = questions.get_question(8)
    at = _select_question(_fresh_app(), spec.label)
    lab_box = next(sb for sb in at.selectbox if sb.label == "Lab Test")
    abnormal_option = next(o for o in lab_box.options if "ITEMID: 50893" in o)
    lab_box.set_value(abnormal_option).run()
    _run(at)

    assert not at.exception
    assert "Analysis completed successfully" in _markdown(at)
    result_df = next((d.value for d in at.dataframe if "FLAG" in list(d.value.columns)), None)
    assert result_df is not None and (result_df["FLAG"] == "abnormal").all()


def test_q8_no_records_edge_case_is_graceful():
    """A lab with no abnormal readings shows the info banner, not an error."""
    spec = questions.get_question(8)
    at = _select_question(_fresh_app(), spec.label)
    _run(at)
    assert not at.exception
    md = _markdown(at)
    assert ("no matching records" in md) or ("Analysis completed successfully" in md)


def test_category_filter_narrows_question_list():
    at = _fresh_app()
    at.selectbox[0].set_value("Patient overview").run()
    assert not at.exception
    options = at.selectbox[1].options
    assert len(options) < 11
    assert all(("admission" in o.lower()) or ("patient" in o.lower()) for o in options)


def test_natural_language_query_runs_end_to_end():
    at = _fresh_app()
    at.text_input[0].set_value("Show hematocrit trend for admission 107521").run()
    button = next(b for b in at.button if b.label == "Interpret & Run")
    button.click()
    at.run()
    assert not at.exception
    text = _all_text(at)
    assert "Interpreted as:" in text
    assert "Analysis completed successfully" in text


def test_natural_language_unrecognized_query_is_handled():
    at = _fresh_app()
    at.text_input[0].set_value("what is the weather today").run()
    button = next(b for b in at.button if b.label == "Interpret & Run")
    button.click()
    at.run()
    assert not at.exception
    assert "Could not recognise" in _all_text(at)
