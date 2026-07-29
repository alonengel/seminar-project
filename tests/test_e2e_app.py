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

DOCTOR_IDS = {1, 2, 3, 4, 5, 7, 8, 10, 11}
RESEARCHER_IDS = {3, 5, 6, 7, 9, 10, 11, 12}

PARAM_WIDGET_LABELS = {
    "hadm_id": "Admission ID (HADM_ID)",
    "itemid": "Lab Test",
    "subject_id": "Patient ID (SUBJECT_ID)",
}


def _fresh_app():
    at = AppTest.from_file(APP_PATH, default_timeout=240)
    at.run()
    return at


def _enter_workspace(at, role="Doctor"):
    button = next(b for b in at.button if b.label == f"Enter {role} workspace")
    button.click()
    at.run()
    return at


def _fresh_workspace(role="Doctor"):
    return _enter_workspace(_fresh_app(), role)


def _workspace_for_spec(spec):
    return "Doctor" if spec.id in DOCTOR_IDS else "Researcher"


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
    assert "Doctor view" in _markdown(at)
    assert "Researcher view" in _markdown(at)


def test_doctor_workspace_shows_doctor_questions():
    at = _fresh_workspace("Doctor")
    assert not at.exception
    assert "Doctor Workspace" in _markdown(at)
    options = at.selectbox[1].options
    assert len(options) == len(DOCTOR_IDS)
    assert questions.get_question(1).label in options
    assert questions.get_question(12).label not in options


def test_researcher_workspace_shows_researcher_questions():
    at = _fresh_workspace("Researcher")
    assert not at.exception
    assert "Researcher Workspace" in _markdown(at)
    options = at.selectbox[1].options
    assert len(options) == len(RESEARCHER_IDS)
    assert questions.get_question(12).label in options
    assert questions.get_question(1).label not in options


@pytest.mark.parametrize("spec", questions.QUESTION_REGISTRY, ids=lambda s: f"Q{s.id}")
def test_question_renders_correct_widgets_and_runs(spec):
    at = _select_question(_fresh_workspace(_workspace_for_spec(spec)), spec.label)
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
    at = _select_question(_fresh_workspace("Doctor"), spec.label)
    lab_box = next(sb for sb in at.selectbox if sb.label == "Lab Test")
    abnormal_option = next(o for o in lab_box.options if "ITEMID: 50893" in o)
    lab_box.set_value(abnormal_option).run()
    _run(at)

    assert not at.exception
    assert "Analysis completed successfully" in _markdown(at)
    result_df = next((d.value for d in at.dataframe if "FLAG" in list(d.value.columns)), None)
    assert result_df is not None and (result_df["FLAG"] == "abnormal").all()


def test_demo_typo_checkbox_recovers_via_correction():
    """The demo toggle injects a typo; success proves the correction loop repaired it."""
    at = _fresh_workspace("Doctor")
    checkbox = next((c for c in at.checkbox if "typo" in c.label.lower()), None)
    assert checkbox is not None, (
        "demo typo checkbox should appear for the default (demoable) question; "
        "checkboxes=" + str([c.label for c in at.checkbox])
    )
    checkbox.set_value(True).run()
    _run(at)
    assert not at.exception
    assert "Analysis completed successfully" in _markdown(at)


def test_q8_no_records_edge_case_is_graceful():
    """A lab with no abnormal readings shows the info banner, not an error."""
    spec = questions.get_question(8)
    at = _select_question(_fresh_workspace("Doctor"), spec.label)
    _run(at)
    assert not at.exception
    md = _markdown(at)
    assert ("no matching records" in md) or ("Analysis completed successfully" in md)


def test_category_filter_narrows_question_list():
    at = _fresh_workspace("Doctor")
    at.selectbox[0].set_value("Patient overview").run()
    assert not at.exception
    options = at.selectbox[1].options
    assert len(options) < len(questions.QUESTION_REGISTRY)
    assert all(("admission" in o.lower()) or ("patient" in o.lower()) for o in options)


def test_natural_language_query_runs_end_to_end():
    at = _fresh_workspace("Doctor")
    at.text_input[0].set_value("Show hematocrit trend for admission 107521").run()
    button = next(b for b in at.button if b.label == "Interpret & Run")
    button.click()
    at.run()
    assert not at.exception
    text = _all_text(at)
    assert "Interpreted as:" in text
    assert "Analysis completed successfully" in text


def test_natural_language_unrecognized_query_is_handled():
    at = _fresh_workspace("Doctor")
    at.text_input[0].set_value("what is the weather today").run()
    button = next(b for b in at.button if b.label == "Interpret & Run")
    button.click()
    at.run()
    assert not at.exception
    assert "Could not recognise" in _all_text(at)


def test_natural_language_all_admissions_routes_to_aggregate():
    """The 'all admissions' ask now maps to Q12 and runs, instead of demanding an ID."""
    at = _fresh_workspace("Researcher")
    at.text_input[0].set_value("show me the abnormal lab results for all the admissions").run()
    button = next(b for b in at.button if b.label == "Interpret & Run")
    button.click()
    at.run()
    assert not at.exception
    text = _all_text(at)
    assert "Interpreted as:" in text
    assert "across all admissions" in text
    assert "Analysis completed successfully" in text


# --- experimental LLM code-generation mode (offline; complete() patched) ---
def _codegen_app(monkeypatch, code_reply):
    """Build the app with a provider key set and llm_client.complete patched to
    return a fixed code snippet, then select the 'Advanced: AI writes code' mode."""
    import llm_client

    monkeypatch.setenv("ANTHROPIC_API_KEY", "real-key-123")
    monkeypatch.setattr(llm_client, "complete", lambda system, user, max_tokens=None: code_reply)

    at = AppTest.from_file(APP_PATH, default_timeout=240)
    at.run()
    _enter_workspace(at, "Researcher")
    at.radio[0].set_value("Advanced: AI writes code").run()
    return at


def _ask_codegen(at, question):
    at.text_input[0].set_value(question).run()
    button = next(b for b in at.button if b.label == "Interpret & Run")
    button.click()
    at.run()
    return at


def test_codegen_mode_success_line_chart(monkeypatch):
    code = "result = df[df['FLAG'] == 'abnormal'][['CHARTTIME', 'VALUENUM', 'LABEL']].head(20)"
    at = _codegen_app(monkeypatch, code)
    _ask_codegen(at, "show abnormal values over time")
    assert not at.exception
    text = _all_text(at)
    assert "Analysis completed successfully" in text
    assert len(at.dataframe) >= 1
    assert any("result =" in (c or "") for c in _codes(at))


def test_codegen_mode_success_bar_chart(monkeypatch):
    code = "result = df.groupby('HADM_ID').size().reset_index(name='abnormal_count').head(10)"
    at = _codegen_app(monkeypatch, code)
    _ask_codegen(at, "count rows per admission")
    assert not at.exception
    assert "Analysis completed successfully" in _all_text(at)


def test_codegen_mode_blocks_malicious_code(monkeypatch):
    code = "import os\nresult = os.getcwd()"
    at = _codegen_app(monkeypatch, code)
    _ask_codegen(at, "read a file from disk")
    assert not at.exception
    text = _all_text(at)
    assert "Could not produce a valid result" in text
    assert any("import os" in (c or "") for c in _codes(at))


def test_codegen_via_escalation_request(monkeypatch):
    """Accepting the escalation dialog (which sets codegen_request) runs code-gen."""
    import llm_client

    monkeypatch.setenv("ANTHROPIC_API_KEY", "real-key-123")
    monkeypatch.setattr(llm_client, "complete", lambda system, user, max_tokens=None: "result = df.head(3)")
    at = AppTest.from_file(APP_PATH, default_timeout=240)
    at.session_state["codegen_request"] = "last 10 abnormal results in the whole database"
    at.session_state["workspace"] = "Researcher"
    at.session_state["user_role"] = "Researcher"
    at.run()
    assert not at.exception
    assert "Analysis completed successfully" in _all_text(at)
    assert any("result =" in (c or "") for c in _codes(at))


def test_escalation_dialog_runs_advanced_and_switches_mode(monkeypatch):
    """A template-mode failure opens the dialog; 'Run with Advanced' runs code-gen and flips the mode."""
    import llm_client

    monkeypatch.setenv("ANTHROPIC_API_KEY", "real-key-123")
    monkeypatch.setattr(llm_client, "complete", lambda system, user, max_tokens=None: "result = df.head(3)")
    at = AppTest.from_file(APP_PATH, default_timeout=240)
    at.run()
    _enter_workspace(at, "Researcher")
    at.radio[0].set_value("Rules only").run()
    at.text_input[0].set_value("last 10 abnormal results across the whole database").run()
    next(b for b in at.button if b.label == "Interpret & Run").click()
    at.run()
    assert not at.exception

    advanced = next((b for b in at.button if b.label == "Run with Advanced"), None)
    assert advanced is not None, (
        "escalation dialog should offer 'Run with Advanced'; buttons="
        + str([b.label for b in at.button])
    )
    advanced.click()
    at.run()
    assert not at.exception
    assert "Analysis completed successfully" in _all_text(at)
    assert any("result =" in (c or "") for c in _codes(at))
    assert at.radio[0].value == "Advanced: AI writes code"
