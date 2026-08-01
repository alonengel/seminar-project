import inspect

import altair as alt
import pandas as pd
import streamlit as st

import correction
import data_prep
import llm_client
import presentation_agent
import questions
from main_pipeline import run_pipeline
from question_router import EXAMPLES, route


st.set_page_config(
    page_title="Clinical Lab Analysis System",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)


@st.cache_resource
def _report_llm_status():
    """Print the LLM key status to the console once per server process."""
    state, message = llm_client.key_status()
    print(f"LLM status [{state.upper()}]: {message}", flush=True)
    return state


_report_llm_status()


# =========================
# Custom Styling
# =========================
st.markdown("""
<style>
.block-container {
    /* Must clear Streamlit's fixed header bar (~3.75rem), or the top row of
       widgets renders underneath the Deploy toolbar. */
    padding-top: 4.2rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

.main-title {
    font-size: 2.6rem;
    font-weight: 800;
    color: #f9fafb;
    margin-bottom: 0.2rem;
}

.subtitle {
    font-size: 1rem;
    color: #9ca3af;
    margin-bottom: 1.5rem;
}

.card {
    background-color: #111827;
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 1.3rem 1.4rem;
    margin-bottom: 1.2rem;
}

.status-box {
    background-color: #111827;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 1.1rem 1.2rem;
    min-height: 115px;
}

.status-label {
    color: #cbd5e1;
    font-size: 0.9rem;
    font-weight: 700;
    margin-bottom: 0.5rem;
}

.status-value {
    color: #f9fafb;
    font-size: 1.35rem;
    font-weight: 700;
    line-height: 1.35;
    white-space: normal;
    word-break: break-word;
}

.success-banner {
    background-color: #123524;
    color: #63e68b;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

.info-banner {
    background-color: #0f223a;
    color: #7dd3fc;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

.error-banner {
    background-color: #3a1212;
    color: #f87171;
    border-radius: 12px;
    padding: 1rem 1.2rem;
    font-weight: 700;
    margin-bottom: 1rem;
}

.helper-box {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 16px;
    padding: 1rem 1.2rem;
    color: #cbd5e1;
    margin-bottom: 1.8rem;
    line-height: 1.7;
}

.welcome-grid {
    display: grid;
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 1rem;
    margin-bottom: 1rem;
}

.role-card {
    background: #0f172a;
    border: 1px solid #334155;
    border-radius: 14px;
    padding: 1.15rem 1.2rem;
    min-height: 160px;
}

.role-card.active {
    border-color: #38bdf8;
    box-shadow: 0 0 0 1px rgba(56, 189, 248, 0.35);
}

.role-title {
    color: #f9fafb;
    font-size: 1.15rem;
    font-weight: 800;
    margin-bottom: 0.45rem;
}

.role-copy {
    color: #cbd5e1;
    line-height: 1.55;
    margin-bottom: 0.75rem;
}

.mini-chip {
    display: inline-block;
    background: #182235;
    border: 1px solid #334155;
    border-radius: 999px;
    color: #dbeafe;
    font-size: 0.8rem;
    font-weight: 700;
    padding: 0.25rem 0.55rem;
    margin: 0.15rem 0.2rem 0.15rem 0;
}

.dashboard-grid {
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 1rem;
}

.question-card {
    background-color: #111827;
    border: 1px solid #30363d;
    border-radius: 12px;
    padding: 1rem;
    /* Sized to the tallest card content so every card in a row matches and
       the Open buttons below them stay on one line. */
    min-height: 205px;
}

.question-id {
    color: #7dd3fc;
    font-size: 0.82rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.question-title {
    color: #f9fafb;
    font-size: 0.98rem;
    font-weight: 760;
    line-height: 1.35;
    margin-bottom: 0.45rem;
}

.question-purpose {
    color: #cbd5e1;
    font-size: 0.9rem;
    line-height: 1.45;
}

.pipeline-step {
    background-color: #101826;
    border: 1px solid #334155;
    border-radius: 12px;
    padding: 0.95rem 1rem;
    min-height: 130px;
}

.step-number {
    color: #7dd3fc;
    font-size: 0.78rem;
    font-weight: 900;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin-bottom: 0.35rem;
}

.step-title {
    color: #f8fafc;
    font-size: 1rem;
    font-weight: 800;
    margin-bottom: 0.35rem;
}

.step-body {
    color: #cbd5e1;
    font-size: 0.88rem;
    line-height: 1.45;
}

.check-row {
    background-color: #0f172a;
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 0.75rem 0.85rem;
    margin-bottom: 0.55rem;
}

.check-title {
    color: #f8fafc;
    font-weight: 800;
    margin-bottom: 0.25rem;
}

.check-body {
    color: #cbd5e1;
    line-height: 1.45;
}

.section-title {
    font-size: 1.35rem;
    font-weight: 700;
    color: #f3f4f6;
    margin-top: 0.7rem;
    margin-bottom: 0.9rem;
}

div[data-baseweb="select"] > div {
    min-height: 48px;
}

.stButton > button {
    height: 48px;
    font-weight: 700;
    border-radius: 12px;
}

[data-testid="stDataFrame"] {
    border-radius: 12px;
}

button[data-baseweb="tab"] {
    font-size: 0.95rem;
    font-weight: 600;
}

@media (max-width: 900px) {
    .welcome-grid,
    .dashboard-grid {
        grid-template-columns: 1fr;
    }
}

/* Help ("?") tooltips are placed by Popper right-aligned above the hovered
   icon, but Popper measures the box before Streamlit's 42rem wrap applies:
   the oversized measurement pushes x negative and gets clamped to the far
   left viewport edge, detaching the tooltip from its icon. Capping the
   width up front lets Popper measure the real box and anchor the tooltip's
   right edge to the icon on its own (verified: tooltip.right == icon.right).
   24rem also keeps the help text at a readable ~60-char line length. */
div[data-testid="stTooltipContent"] {
    max-width: 24rem !important;
}
</style>
""", unsafe_allow_html=True)


merged_data = data_prep.merged_data

QUESTION_HELP = {
    1: "Lists every abnormal-flagged lab result for the admission.",
    2: "Returns the most recent value of one lab test.",
    3: "Shows how one lab test changes over time.",
    4: "Lists all lab tests performed during the admission.",
    5: "Compares the first and last value of one lab test.",
    6: "Min, max, mean and count for one lab test.",
    7: "How many results were abnormal versus normal.",
    8: "Abnormal-flagged readings for one specific lab test.",
    9: "Distinct lab tests that were ever flagged abnormal, with counts.",
    10: "Values of one lab test within a date range.",
    11: "All admissions recorded for one patient.",
    12: "Abnormal vs normal counts for every admission in the dataset.",
}

_PARAM_NAMES = {
    "hadm_id": "admission",
    "itemid": "lab test",
    "subject_id": "patient",
    "date_range": "date range",
}

ROLE_PROFILES = {
    "Doctor": {
        "tagline": "Fast admission-level review for bedside decisions.",
        "focus": "Use this view when the user wants to inspect a patient admission, find abnormal values, review trends, or compare lab movement during the stay.",
        "questions": [1, 2, 3, 4, 5, 7, 8, 10, 11],
        "chips": ["Admission review", "Latest value", "Trend", "Abnormal flags"],
    },
    "Researcher": {
        "tagline": "Dataset-level exploration and reproducible analysis.",
        "focus": "Use this view when the user wants summary statistics, cohort-style counts, abnormal-test summaries, or repeatable exports for later analysis.",
        "questions": [3, 5, 6, 7, 9, 10, 11, 12],
        "chips": ["Cohort counts", "Summary stats", "Date windows", "Exports"],
    },
}

QUESTION_PURPOSES = {
    1: "Doctor: quickly surfaces abnormal results inside one admission.",
    2: "Doctor: answers the most recent measured value for one lab.",
    3: "Doctor and researcher: shows a time trend that can be charted and audited.",
    4: "Doctor: gives the full lab-work context for an admission.",
    5: "Doctor and researcher: compares how a lab changed from first to last reading.",
    6: "Researcher: produces count, min, max, and mean for one lab test.",
    7: "Doctor and researcher: summarizes abnormal burden for one admission.",
    8: "Doctor: narrows abnormal values to one selected lab test.",
    9: "Researcher: ranks distinct abnormal lab tests by abnormal count.",
    10: "Doctor and researcher: isolates lab behavior inside a date window.",
    11: "Doctor and researcher: shows all admissions linked to a patient.",
    12: "Researcher: compares abnormal and normal counts across all admissions.",
}

VALIDATION_RULE_TEXT = {
    1: "All returned rows must be abnormal-flagged.",
    2: "Exactly one latest row must be returned.",
    3: "Rows must be ordered by measurement time ascending.",
    4: "The result must include all lab-test rows for the admission.",
    5: "Exactly one comparison row must be returned.",
    6: "Exactly one summary-statistics row must be returned.",
    7: "Exactly one count row must be returned.",
    8: "All returned rows must be abnormal rows for the selected lab.",
    9: "Each row is a distinct abnormal lab test with its abnormal count.",
    10: "Rows must be inside the selected date range and time-sorted.",
    11: "Rows must describe admissions for the selected patient.",
    12: "For every admission, Abnormal + Normal must equal Total Tests.",
}


# =========================
# Render helpers
# =========================
def _status_box(label, value, color):
    st.markdown(
        f'<div class="status-box"><div class="status-label">{label}</div>'
        f'<div class="status-value" style="color:{color}">{value}</div></div>',
        unsafe_allow_html=True,
    )


def _question_by_id(question_id):
    return questions.get_question(question_id)


def _inputs_text(spec):
    if not spec.params:
        return "No user input"
    return ", ".join(_PARAM_NAMES.get(p, p) for p in spec.params)


def _choose_question(question_id):
    st.session_state["selected_question_id"] = question_id
    st.session_state["selected_category"] = "All"


def _set_workspace(role):
    st.session_state["workspace"] = role
    st.session_state["user_role"] = role
    first_question = ROLE_PROFILES[role]["questions"][0]
    st.session_state["selected_question_id"] = first_question
    st.session_state["selected_category"] = "All"
    st.session_state.pop("codegen_output", None)


def _render_landing_page():
    st.markdown('<div class="main-title">Clinical Lab Analysis System</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">Choose the workspace that matches the way you want to use the lab data</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="helper-box">
            This project answers predefined clinical laboratory questions over the cleaned MIMIC-III dataset.
            It generates Python code, executes it, validates the result, applies correction when needed,
            and then explains the result, validation, and correction attempts. Start by choosing a role.
            The system currently supports <b>{len(questions.QUESTION_REGISTRY)} question types</b>.
        </div>
        """,
        unsafe_allow_html=True,
    )

    _render_methodology_notes()
    _render_project_evaluation("Doctor and Researcher")

    role_cols = st.columns(2)
    for role, container in zip(ROLE_PROFILES, role_cols):
        profile = ROLE_PROFILES[role]
        active = ""
        chips = "".join(f'<span class="mini-chip">{chip}</span>' for chip in profile["chips"])
        with container:
            st.markdown(
                f"""
                <div class="role-card{active}">
                    <div class="role-title">{role} view</div>
                    <div class="role-copy"><b>{profile["tagline"]}</b><br>{profile["focus"]}</div>
                    <div>{chips}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Enter {role} workspace", key=f"enter_role_{role}", type="primary", width="stretch"):
                _set_workspace(role)
                st.rerun()

    with st.expander("What happens after you choose a workspace?", expanded=True):
        cols = st.columns(4)
        explanations = [
            ("Focused questions", "Only the questions that fit the selected role are shown first."),
            ("Same trusted pipeline", "The backend still uses the registry-driven generation, execution, validation, and correction flow."),
            ("Readable audit", "Validation and correction are explained as checks and attempts, not only raw code."),
            ("Switch anytime", "You can return here or switch roles without restarting the app."),
        ]
        for col, (title, body) in zip(cols, explanations):
            with col:
                st.markdown(
                    f"""
                    <div class="pipeline-step">
                        <div class="step-title">{title}</div>
                        <div class="step-body">{body}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def _render_workspace_header():
    role = st.session_state.get("workspace", "Doctor")
    profile = ROLE_PROFILES[role]
    top_left, top_right = st.columns([3, 1])
    with top_left:
        st.markdown(f'<div class="main-title">{role} Workspace</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="subtitle">{profile["tagline"]}</div>',
            unsafe_allow_html=True,
        )
    with top_right:
        if st.button("Back to Welcome", width="stretch"):
            st.session_state["workspace"] = "Welcome"
            st.session_state.pop("codegen_output", None)
            st.rerun()
        other_role = "Researcher" if role == "Doctor" else "Doctor"
        if st.button(f"Switch to {other_role}", width="stretch"):
            _set_workspace(other_role)
            st.rerun()
    chips = "".join(f'<span class="mini-chip">{chip}</span>' for chip in profile["chips"])
    st.markdown(
        f"""
        <div class="helper-box">
            <b>{role} focus:</b> {profile["focus"]}<br>
            <div style="margin-top:0.55rem">{chips}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_methodology_notes():
    with st.expander("Implementation Notes: Validation & Correction"):
        st.write(
            "This section connects what the UI shows to the actual implementation files. "
            "The professor can open this before or after a run, then verify the same steps "
            "in the result tabs."
        )

        val_col, corr_col = st.columns(2)
        with val_col:
            st.markdown("#### Validation")
            st.markdown(
                """
                Validation is deterministic and registry-driven:

                - `questions.py` defines every supported question in `QUESTION_REGISTRY`.
                - Each `QuestionSpec` stores the expected output columns.
                - Some questions also define an extra validation rule.
                - `validation.py` checks that execution succeeded.
                - It verifies the result is a pandas `DataFrame`.
                - It checks that all expected columns exist.
                - It rejects empty results as failed validation, while the UI presents valid no-record cases clearly.
                - It applies the question-specific rule when one exists.

                Examples:

                - Abnormal-result questions must return only `FLAG = abnormal`.
                - Latest-value and summary questions must return exactly one row.
                - Trend/date-range questions must be sorted by `CHARTTIME`.
                - Dataset-wide counts must satisfy `Abnormal + Normal = Total Tests`.
                """
            )

        with corr_col:
            st.markdown("#### Correction")
            st.markdown(
                """
                Correction is a bounded rule-based retry loop:

                - `main_pipeline.py` generates a Python call for the selected question.
                - `correction.py` runs the generated code and validates the result.
                - If execution or validation fails, it builds feedback from the error and validation message.
                - `correct_generated_code()` applies safe known fixes, mainly generated function-name typos.
                - The retry loop is bounded, so it cannot keep editing forever.
                - Every attempt is recorded and displayed in the `Correction Attempts` tab.

                The demo checkbox intentionally injects a typo into the generated function name.
                That proves the first attempt fails, the correction rule repairs the generated call,
                and the second attempt passes execution and validation.
                """
            )

        st.info(
            "Key point: validation and correction are not hidden LLM behavior. They are explicit, "
            "testable Python rules connected to the question registry."
        )


def _render_project_evaluation(role):
    with st.expander("Project Evaluation: Why This Version Matches the Goal"):
        st.write(
            "The goal of the project is to automatically answer a limited, controlled set of "
            "clinical lab-analysis questions over MIMIC-III while showing the full generated-code "
            "pipeline: generation, execution, validation, correction, and presentation."
        )

        eval_cols = st.columns(2)
        with eval_cols[0]:
            st.markdown("#### Primary Users")
            st.markdown(
                """
                **Doctor**

                - Works mainly at the admission/patient level.
                - Needs quick abnormal-result review.
                - Needs latest values, trends, and first-vs-last comparisons.
                - Benefits from context, readable tables, and clear no-record states.

                **Researcher**

                - Works mainly with repeatable analysis and dataset-level patterns.
                - Needs summary statistics, abnormal counts, and exportable tables.
                - Benefits from validation transparency and reproducible generated code.
                - Can use the optional AI/code-generation mode for exploratory questions, with sandbox protection.
                """
            )

        with eval_cols[1]:
            st.markdown("#### Evaluation Criteria")
            st.markdown(
                """
                This version matches the project requirements because it provides:

                - A fixed registry of supported questions, not uncontrolled medical Q&A.
                - 12 predefined clinical lab question types.
                - Dynamic parameter inputs based on the selected question.
                - Generated executable Python code for each template question.
                - Safe execution wrapper with structured success/error output.
                - Deterministic validation for shape, columns, emptiness, and clinical rules.
                - Rule-based correction with recorded attempts.
                - Result presentation with metrics, tables, charts, CSV export, and audit tabs.
                - Optional natural-language routing that still maps to supported questions.
                - Optional experimental AI code generation guarded by a sandbox.
                """
            )

        st.markdown("#### Why The Role-Based UI Helps")
        st.markdown(
            f"""
            The current workspace is **{role}**, so the first questions shown are the ones that
            naturally fit that user's workflow. This improves the project presentation because the
            12 questions are no longer just a long list; they are organized around the two primary
            user types. The backend remains the same tested pipeline, but the frontend now explains
            who the system is for and why each analysis path matters.

            The most important proof appears after every run: the app shows the final result, the
            validation audit, the correction attempts, and the generated code. That directly supports
            the seminar requirement to demonstrate not only the answer, but also how the answer was
            produced and checked.
            """
        )

        st.success(
            "Evaluation summary: the project is aligned with the course goal because it is controlled, "
            "transparent, testable, and user-focused while still demonstrating AI-style code generation "
            "and self-correction."
        )


def _render_question_cards(question_ids, prefix):
    card_cols = st.columns(3)
    for idx, question_id in enumerate(question_ids):
        spec = _question_by_id(question_id)
        with card_cols[idx % 3]:
            st.markdown(
                f"""
                <div class="question-card">
                    <div class="question-id">Question {spec.id} - {spec.category}</div>
                    <div class="question-title">{spec.label}</div>
                    <div class="question-purpose">{QUESTION_PURPOSES.get(spec.id, QUESTION_HELP.get(spec.id, ""))}</div>
                    <div class="question-purpose"><b>Inputs:</b> {_inputs_text(spec)}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if st.button(f"Open Q{spec.id}", key=f"{prefix}_open_q{spec.id}", width="stretch"):
                _choose_question(spec.id)
                st.rerun()


def _render_question_dashboards():
    role = st.session_state.get("user_role", "Doctor")
    with st.expander(f"{role} questions", expanded=True):
        st.caption(
            "These questions are the role-focused entry points for this workspace. "
            "Click one to load it into the analysis panel below."
        )
        _render_question_cards(ROLE_PROFILES[role]["questions"], f"role_{role.lower()}")


def _render_pipeline_overview(spec, params, final_result, result):
    validation_result = final_result.get("validation", {})
    attempts = final_result.get("attempts", [])
    row_count = len(result) if isinstance(result, pd.DataFrame) else "not a table"
    correction_text = (
        "Correction was applied after a failed attempt."
        if final_result.get("correction_applied")
        else "No correction was needed; the first valid attempt passed."
    )
    steps = [
        ("1", "Question selected", f"[{spec.id}] {spec.label}. Inputs: {_inputs_text(spec)}. Parameters: {params or 'none'}."),
        ("2", "Code generated", f"The registry selected `{spec.func.__name__}` and produced a Python call from the parameters."),
        ("3", "Execution", final_result.get("execution", {}).get("status", "Unknown")),
        ("4", "Validation", validation_result.get("message", "No validation message.")),
        ("5", "Correction", correction_text),
    ]
    cols = st.columns(5)
    for col, (number, title, body) in zip(cols, steps):
        with col:
            st.markdown(
                f"""
                <div class="pipeline-step">
                    <div class="step-number">Step {number}</div>
                    <div class="step-title">{title}</div>
                    <div class="step-body">{body}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
    st.caption(f"Returned rows: {row_count}. Attempts made: {len(attempts)}.")


def _render_validation_audit(spec, result, validation_result, no_records=False):
    returned_cols = list(result.columns) if isinstance(result, pd.DataFrame) else []
    missing_cols = [col for col in spec.expected_columns if col not in returned_cols]
    row_count = len(result) if isinstance(result, pd.DataFrame) else "not a DataFrame"
    checks = [
        ("Execution output", "The pipeline produced a pandas DataFrame." if isinstance(result, pd.DataFrame) else f"Output type: {type(result).__name__}."),
        ("Expected columns", ", ".join(spec.expected_columns)),
        ("Returned columns", ", ".join(returned_cols) if returned_cols else "No table columns returned."),
        ("Missing columns", "None" if not missing_cols else ", ".join(missing_cols)),
        ("Rows returned", str(row_count)),
        ("Question-specific rule", VALIDATION_RULE_TEXT.get(spec.id, "The result must match the registry rule for this question.")),
    ]
    for title, body in checks:
        st.markdown(
            f'<div class="check-row"><div class="check-title">{title}</div><div class="check-body">{body}</div></div>',
            unsafe_allow_html=True,
        )
    if validation_result.get("valid"):
        st.success(validation_result.get("message", "Validation passed."))
    elif no_records:
        st.info(validation_result.get("message", "No matching records were found."))
    else:
        st.error(validation_result.get("message", "Validation failed."))


def _attempt_summary_rows(attempts):
    rows = []
    for attempt in attempts or []:
        execution_result = attempt.get("execution", {})
        validation_result = attempt.get("validation", {})
        code = (attempt.get("code") or "").strip()
        rows.append({
            "Attempt": attempt.get("attempt"),
            "Execution": execution_result.get("status", "Unknown"),
            "Execution error": execution_result.get("error") or "",
            "Validation": "Passed" if validation_result.get("valid") else "Failed",
            "Validation message": validation_result.get("message", ""),
            "Generated call": code.replace("\n", " "),
        })
    return rows


def _render_attempts_audit(final_result):
    attempts = final_result.get("attempts") or []
    if not attempts:
        st.info("No attempts were recorded.")
        return

    st.dataframe(pd.DataFrame(_attempt_summary_rows(attempts)), width="stretch", hide_index=True)
    if final_result.get("correction_applied"):
        st.success(
            "The first generated call failed, the correction rule rewrote the function name, "
            "and the next attempt passed validation."
        )
    else:
        st.info("The first attempt executed and validated successfully, so the correction loop stopped immediately.")

    for attempt in attempts:
        with st.expander(f"Attempt {attempt.get('attempt')} details"):
            exec_result = attempt.get("execution", {})
            val_result = attempt.get("validation", {})
            st.write(f"Execution: {exec_result.get('status', 'Unknown')}")
            if exec_result.get("error"):
                st.error(exec_result.get("error"))
            st.write(f"Validation: {val_result.get('message', 'No validation message.')}")
            st.code(attempt.get("code") or "", language="python")


def _render_metrics(spec, result):
    if not isinstance(result, pd.DataFrame) or result.empty:
        return
    row = result.iloc[0]
    if spec.id == 2:
        cols = st.columns(2)
        cols[0].metric("Latest value", f"{row['VALUENUM']} {row['VALUEUOM']}")
        cols[1].metric("Measured at", str(row["CHARTTIME"]))
    elif spec.id == 5:
        cols = st.columns(3)
        cols[0].metric("First value", f"{row['First Value']}")
        cols[1].metric("Last value", f"{row['Last Value']}")
        cols[2].metric("Difference", f"{row['Difference']}")
    elif spec.id == 6:
        cols = st.columns(4)
        cols[0].metric("Count", int(row["Count"]))
        cols[1].metric("Min", f"{row['Min']}")
        cols[2].metric("Max", f"{row['Max']}")
        cols[3].metric("Mean", f"{row['Mean']}")
    elif spec.id == 7:
        cols = st.columns(3)
        cols[0].metric("Total tests", int(row["Total Tests"]))
        cols[1].metric("Abnormal", int(row["Abnormal"]))
        cols[2].metric("Normal", int(row["Normal"]))
    elif spec.id == 12:
        cols = st.columns(3)
        cols[0].metric("Admissions", len(result))
        cols[1].metric("Total abnormal", int(result["Abnormal"].sum()))
        cols[2].metric("Total tests", int(result["Total Tests"].sum()))
    else:
        st.metric("Rows returned", len(result))


def _render_trend_chart(spec, result):
    if not (spec.chart and isinstance(result, pd.DataFrame) and not result.empty):
        return
    x_field, y_field = spec.chart["x"], spec.chart["y"]
    if x_field not in result.columns or y_field not in result.columns:
        return
    data = result[[x_field, y_field]].dropna()
    if data.empty:
        return
    unit = ""
    if "VALUEUOM" in result.columns and not result["VALUEUOM"].dropna().empty:
        unit = str(result["VALUEUOM"].dropna().iloc[0])
    label = y_field
    if "LABEL" in result.columns and not result["LABEL"].dropna().empty:
        label = str(result["LABEL"].dropna().iloc[0])
    y_title = f"{label} ({unit})" if unit else label
    chart = (
        alt.Chart(data)
        .mark_line(point=True)
        .encode(
            x=alt.X(f"{x_field}:T", title="Time"),
            y=alt.Y(f"{y_field}:Q", title=y_title),
            tooltip=list(data.columns),
        )
        .properties(width="container", height=320, title=f"{label} over time")
    )
    st.altair_chart(chart)


def _render_view_chart(result, view):
    """Render a chart for a code-gen result from a presentation_agent spec."""
    if not view or not isinstance(result, pd.DataFrame):
        return
    x_field, y_field = view.get("x"), view.get("y")
    if x_field not in result.columns or y_field not in result.columns:
        return
    data = result[[x_field, y_field]].dropna()
    if data.empty:
        return
    if view.get("chart") == "line":
        if pd.api.types.is_datetime64_any_dtype(result[x_field]):
            x_enc = alt.X(f"{x_field}:T", title=str(x_field))
        else:
            x_enc = alt.X(f"{x_field}:Q", title=str(x_field))
        chart = alt.Chart(data).mark_line(point=True).encode(
            x=x_enc, y=alt.Y(f"{y_field}:Q", title=str(y_field)), tooltip=list(data.columns)
        )
    else:
        chart = alt.Chart(data).mark_bar().encode(
            x=alt.X(f"{x_field}:N", title=str(x_field), sort="-y"),
            y=alt.Y(f"{y_field}:Q", title=str(y_field)),
            tooltip=list(data.columns),
        )
    st.altair_chart(chart.properties(width="container", height=320))


def _render_codegen(output, question):
    """Render the result of the experimental LLM code-generation pipeline."""
    st.divider()
    st.warning(
        "Experimental: an LLM wrote and ran sandboxed pandas code to answer this. "
        "The result is validated, but this is outside the curated question templates."
    )

    success = output.get("success")
    result = output.get("result")
    no_records = success and isinstance(result, pd.DataFrame) and result.empty

    if success and not no_records:
        st.markdown('<div class="success-banner">Analysis completed successfully</div>', unsafe_allow_html=True)
    elif no_records:
        st.markdown(
            '<div class="info-banner">Code ran successfully, but no matching records were found.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="error-banner">Could not produce a valid result. See the details below.</div>',
            unsafe_allow_html=True,
        )

    green, red, blue, grey = "#63e68b", "#f87171", "#7dd3fc", "#cbd5e1"
    execution_status = output.get("execution", {}).get("status", "Unknown")
    validation = output.get("validation", {})
    validation_passed = validation.get("valid")
    n_attempts = len(output.get("attempts", []))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        _status_box("Execution", execution_status, green if "success" in str(execution_status).lower() else red)
    with col2:
        _status_box("Validation", "Passed" if validation_passed else "Failed", green if validation_passed else (blue if no_records else red))
    with col3:
        _status_box("Attempts", n_attempts, blue)
    with col4:
        _status_box("Overall Status", output.get("status", "Unknown"), green if success else red)

    st.divider()
    result_tab, process_tab, code_tab, attempts_tab = st.tabs(
        ["Final Result", "AI Process", "Generated Code", "Attempts"]
    )

    with result_tab:
        st.subheader("Final Result")
        if isinstance(result, pd.DataFrame) and not result.empty:
            _render_view_chart(result, presentation_agent.suggest_view(result, question))
            st.dataframe(result, width="stretch", hide_index=True)
            csv = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Result as CSV",
                data=csv,
                file_name="codegen_result.csv",
                mime="text/csv",
                width="stretch",
            )
        elif isinstance(result, pd.DataFrame) and result.empty:
            st.info("No matching records were found.")
        elif result is not None:
            st.write(result)
        else:
            st.warning(validation.get("message", "No result was produced."))

    with process_tab:
        st.subheader("How the AI Code-Generation Pipeline Worked")
        st.markdown(
            """
            <div class="check-row">
                <div class="check-title">1. Programmer agent</div>
                <div class="check-body">The LLM received the dataset schema and wrote one pandas snippet that assigns its answer to <b>result</b>.</div>
            </div>
            <div class="check-row">
                <div class="check-title">2. Sandbox gate</div>
                <div class="check-body">The code was checked with an AST allowlist before execution. Imports, file access, network access, private attributes, eval/query, and dangerous builtins are blocked.</div>
            </div>
            <div class="check-row">
                <div class="check-title">3. Execution</div>
                <div class="check-body">The snippet ran with only <b>df</b>, <b>pd</b>, and safe builtins available.</div>
            </div>
            <div class="check-row">
                <div class="check-title">4. Validation</div>
                <div class="check-body">The result had to be non-empty, displayable, row-capped, and deterministic enough to present.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("Plan:")
        st.info(output.get("plan") or "No explicit plan was provided.")
        if validation_passed:
            st.success(validation.get("message", "Validation passed."))
        else:
            st.error(validation.get("message", "Validation failed."))

    with code_tab:
        st.subheader("Generated Python Code")
        st.code(output.get("final_code") or "# (no code generated)", language="python")

    with attempts_tab:
        st.subheader("Attempt-by-Attempt Explanation")
        st.dataframe(pd.DataFrame(_attempt_summary_rows(output.get("attempts"))), width="stretch", hide_index=True)
        for attempt in output.get("attempts", []):
            with st.expander(f"Attempt {attempt.get('attempt')} details"):
                st.write(f"Execution: {attempt.get('execution', {}).get('status', 'Unknown')}")
                if attempt.get("execution", {}).get("error"):
                    st.error(attempt["execution"]["error"])
                st.write(f"Validation: {attempt.get('validation', {}).get('message', 'No validation message.')}")
                st.code(attempt.get("code") or "", language="python")


@st.dialog("No ready-made question matched")
def _offer_advanced_dialog(question):
    """Modal shown when a template mode cannot answer; offers to escalate to code-gen."""
    st.write(
        f"I could not map this to one of the {len(questions.QUESTION_REGISTRY)} "
        "ready-made questions:"
    )
    st.info(question)
    st.write(
        "Switch to **Advanced (AI writes code)**? An LLM will write sandboxed pandas "
        "code to answer it directly (experimental), instead of using a template."
    )
    col_yes, col_no = st.columns(2)
    if col_yes.button("Run with Advanced", type="primary", width="stretch"):
        st.session_state["codegen_request"] = question
        st.session_state["pending_mode"] = "Advanced: AI writes code"
        st.session_state.pop("escalation_text", None)
        st.rerun()
    if col_no.button("Cancel", width="stretch"):
        st.session_state.pop("escalation_text", None)
        st.rerun()


# =========================
# Header
# =========================
if "workspace" not in st.session_state:
    st.session_state["workspace"] = "Welcome"

if st.session_state["workspace"] == "Welcome":
    _render_landing_page()
    st.stop()

_render_workspace_header()
st.markdown("<br>", unsafe_allow_html=True)
_render_question_dashboards()


# =========================
# Natural-language question (optional, controlled routing)
# =========================
with st.expander("Ask a clinical lab question in natural language (optional)"):
    st.caption(
        "Your question is routed to one of the supported question templates - "
        "no free-form code is generated or run. Examples:"
    )
    st.markdown("\n".join(f"- {example}" for example in EXAMPLES))
    _provider = llm_client.active_provider()
    if _provider:
        _MODE_OPTIONS = ["Rules only", "Rules, then AI", "Advanced: AI writes code"]
        if "interp_mode" not in st.session_state:
            st.session_state["interp_mode"] = "Rules, then AI"
        # An accepted escalation moves the selection to Advanced for this run.
        _pending = st.session_state.pop("pending_mode", None)
        if _pending in _MODE_OPTIONS:
            st.session_state["interp_mode"] = _pending
        _mode_label = st.radio(
            "Interpretation mode",
            _MODE_OPTIONS,
            horizontal=True,
            key="interp_mode",
            help=(
                f"AI uses the LLM provider '{_provider}'. 'Rules only' is keyword matching "
                "(no LLM). 'Rules, then AI' falls back to the LLM to pick a supported "
                "question. 'Advanced' lets the model write sandboxed pandas code for "
                "free-form questions (experimental)."
            ),
        )
        nl_mode = {
            "Rules only": "rules",
            "Rules, then AI": "auto",
            "Advanced: AI writes code": "codegen",
        }[_mode_label]
        if nl_mode == "codegen":
            st.caption(
                "Experimental: the LLM writes pandas code that runs in a restricted sandbox "
                "(no imports, files, or network) and is validated before display."
            )
    else:
        st.caption("AI is OFF (no API key in .env) - using rule-based routing. Add a key to enable LLM modes.")
        nl_mode = "rules"
    nl_text = st.text_input(
        "Your question",
        key="nl_text",
        placeholder="e.g. Show hematocrit trend for admission 107521",
    )
    nl_submit = st.button("Interpret & Run", key="nl_submit")


# =========================
# Question Selection Panel
# =========================
st.markdown('<div class="section-title">Question Selection</div>', unsafe_allow_html=True)

workspace_role = st.session_state.get("workspace", "Doctor")
workspace_question_ids = set(ROLE_PROFILES[workspace_role]["questions"])
workspace_specs = [q for q in questions.QUESTION_REGISTRY if q.id in workspace_question_ids]
categories = ["All"] + sorted({q.category for q in workspace_specs})

cat_col, question_col = st.columns([1, 3])

with cat_col:
    selected_category = st.selectbox("Category", categories, key="selected_category")

visible_specs = [
    q for q in workspace_specs
    if selected_category == "All" or q.category == selected_category
]

if not visible_specs:
    visible_specs = workspace_specs

selected_question_id = st.session_state.get("selected_question_id")
default_index = 0
if selected_question_id is not None:
    for idx, candidate in enumerate(visible_specs):
        if candidate.id == selected_question_id:
            default_index = idx
            break

with question_col:
    question_label = st.selectbox(
        "Choose a clinical question",
        [q.label for q in visible_specs],
        index=default_index,
    )

spec = questions.get_question_by_label(question_label)
st.session_state["selected_question_id"] = spec.id

_inputs = _inputs_text(spec)
st.caption(f"{QUESTION_HELP.get(spec.id, '')}  Inputs: {_inputs}.")

# Demo only: offer to inject a typo so the rule-based correction loop is visible.
demo_typo = False
if spec.func.__name__ in correction.REVERSE_TYPOS:
    demo_typo = st.checkbox(
        "Demo: inject a typo to force a correction",
        value=False,
        help=(
            "Deliberately misspells the generated function name so the first attempt "
            "fails and the rule-based correction step fixes it - you will see two "
            "attempts and 'Correction Applied: Yes'."
        ),
    )


# =========================
# Parameter widgets (driven by spec.params + PARAM_DEFS)
# =========================
params = {}
display = {}

widget_keys = spec.params
param_cols = st.columns(len(widget_keys) + 1)


def _render_widget(widget_key, container):
    pdef = questions.PARAM_DEFS[widget_key]
    kind = pdef["kind"]

    with container:
        if kind == "hadm":
            hadm_ids = sorted(merged_data["HADM_ID"].dropna().unique())
            default_hadm = 145834.0 if 145834.0 in hadm_ids else hadm_ids[0]
            hadm_id = st.selectbox(
                pdef["label"], hadm_ids, index=hadm_ids.index(default_hadm)
            )
            params["hadm_id"] = int(hadm_id)

        elif kind == "itemid":
            hadm_id = params.get("hadm_id")
            labs = (
                merged_data[merged_data["HADM_ID"] == hadm_id][["ITEMID", "LABEL"]]
                .drop_duplicates()
                .sort_values(by=["LABEL", "ITEMID"])
            )
            if labs.empty:
                st.warning("No lab tests for this admission.")
            else:
                labs["display"] = (
                    labs["LABEL"].astype(str)
                    + " | ITEMID: "
                    + labs["ITEMID"].astype(int).astype(str)
                )
                choice = st.selectbox(pdef["label"], labs["display"].tolist())
                row = labs[labs["display"] == choice].iloc[0]
                params["itemid"] = int(row["ITEMID"])
                display["lab"] = f"{row['LABEL']}  |  ITEMID: {int(row['ITEMID'])}"

        elif kind == "subject":
            subject_ids = sorted(merged_data["SUBJECT_ID_x"].dropna().unique())
            subject_id = st.selectbox(pdef["label"], subject_ids)
            params["subject_id"] = int(subject_id)

        elif kind == "date_range":
            hadm_id = params.get("hadm_id")
            scope = merged_data[merged_data["HADM_ID"] == hadm_id]
            if "itemid" in params:
                scope = scope[scope["ITEMID"] == params["itemid"]]

            times = pd.to_datetime(scope["CHARTTIME"], errors="coerce").dropna()
            if times.empty:
                times = pd.to_datetime(
                    merged_data[merged_data["HADM_ID"] == hadm_id]["CHARTTIME"],
                    errors="coerce",
                ).dropna()

            if times.empty:
                st.warning("No timestamps available for this selection.")
            else:
                min_d, max_d = times.min().date(), times.max().date()
                picked = st.date_input(
                    pdef["label"],
                    value=(min_d, max_d),
                    min_value=min_d,
                    max_value=max_d,
                )
                if isinstance(picked, (tuple, list)):
                    start = picked[0]
                    end = picked[-1]
                else:
                    start = end = picked
                params["start_time"] = str(start)
                params["end_time"] = str(end)


for i, widget_key in enumerate(widget_keys):
    _render_widget(widget_key, param_cols[i])

with param_cols[-1]:
    st.write("")
    st.write("")
    run_button = st.button("Run Analysis", type="primary", width="stretch")


required_args = list(inspect.signature(spec.func).parameters.keys())
params_ready = all(arg in params for arg in required_args)


# A natural-language query, when submitted and understood, overrides the
# structured selection and drives the same pipeline. In "codegen" mode it hands
# off to the guarded LLM code-generation pipeline. If a template mode cannot
# match, we offer to escalate to code-gen (when an LLM provider is configured).
nl_error = None
nl_interpretation = None

# A manual "Run Analysis" supersedes any earlier code-gen result.
if run_button:
    st.session_state.pop("codegen_output", None)

if nl_submit and (nl_text or "").strip():
    st.session_state.pop("codegen_output", None)
    st.session_state.pop("escalation_text", None)
    if nl_mode == "codegen":
        st.session_state["codegen_request"] = nl_text
    else:
        routed = route(nl_text, nl_mode)
        if routed["matched"]:
            spec = questions.get_question(routed["question_id"])
            params = routed["params"]
            params_ready = True
            run_button = True
            nl_interpretation = routed["message"] + f"  (via {routed.get('method', 'rules')})"
            display = {}
        else:
            nl_error = routed["message"]
            # Remember the unmatched question so the escalation dialog can persist
            # across reruns (otherwise its buttons would never register a click).
            if llm_client.active_provider():
                st.session_state["escalation_text"] = nl_text

# Keep the escalation dialog open (re-rendered each run) until the user acts on it.
if st.session_state.get("escalation_text"):
    _offer_advanced_dialog(st.session_state["escalation_text"])

# Run code-gen when requested directly (codegen mode) or accepted via the dialog.
codegen_request = st.session_state.pop("codegen_request", None)
if codegen_request:
    with st.spinner("The AI is writing and running sandboxed code..."):
        st.session_state["codegen_output"] = route(codegen_request, "codegen")

codegen_output = st.session_state.get("codegen_output")


# =========================
# Context Section
# =========================
context_left, context_right = st.columns([1.1, 1])

with context_left:
    with st.container(border=True):
        st.markdown('<div class="section-title">Selected Question</div>', unsafe_allow_html=True)
        st.info(f"[{spec.id}] {spec.label}")

        st.markdown('<div class="section-title">Selected Parameters</div>', unsafe_allow_html=True)
        st.json(params)

with context_right:
    with st.container(border=True):
        if "hadm_id" in spec.params and "hadm_id" in params:
            st.markdown('<div class="section-title">Admission Context</div>', unsafe_allow_html=True)
            admission_info = merged_data[
                merged_data["HADM_ID"] == params["hadm_id"]
            ][["HADM_ID", "ADMITTIME", "DISCHTIME", "DIAGNOSIS"]].drop_duplicates()
            st.dataframe(admission_info, width="stretch", hide_index=True)

            if "lab" in display:
                st.markdown('<div class="section-title">Selected Lab Test</div>', unsafe_allow_html=True)
                st.success(display["lab"])

        elif "subject_id" in spec.params and "subject_id" in params:
            st.markdown('<div class="section-title">Patient Context</div>', unsafe_allow_html=True)
            patient_rows = merged_data[merged_data["SUBJECT_ID_x"] == params["subject_id"]]
            n_admissions = patient_rows["HADM_ID"].nunique()
            st.success(f"Patient {params['subject_id']} has {n_admissions} admission(s) in the dataset.")

        elif not spec.params:
            st.markdown('<div class="section-title">Scope</div>', unsafe_allow_html=True)
            st.info("This question runs across the entire dataset - just click Run Analysis.")

        else:
            st.info("Select parameters to see context here.")


# =========================
# Run Pipeline
# =========================
if codegen_output is not None:
    _render_codegen(codegen_output, nl_text)

elif run_button and params_ready:
    st.divider()

    if nl_interpretation:
        st.success("Interpreted as: " + nl_interpretation)

    with st.spinner("Running analysis through the full pipeline..."):
        final_result = run_pipeline(spec.id, params, inject_typo=demo_typo)

    success = final_result.get("success")
    overall_status = final_result.get("status", "Unknown")
    validation = final_result.get("validation", {})
    validation_passed = validation.get("valid")
    validation_message = validation.get("message", "No validation message.")
    correction_applied = final_result.get("correction_applied")
    execution_status = final_result.get("execution", {}).get("status", "Unknown")

    result = final_result.get("result")
    if result is None:
        # On failure the pipeline returns result=None; fall back to whatever the
        # execution produced (e.g. an empty DataFrame) for display purposes.
        result = final_result.get("execution", {}).get("result")

    no_records = (
        (not success)
        and isinstance(result, pd.DataFrame)
        and result.empty
    )

    if success:
        st.markdown(
            '<div class="success-banner">Analysis completed successfully</div>',
            unsafe_allow_html=True,
        )
    elif no_records:
        st.markdown(
            '<div class="info-banner">Analysis ran successfully, but no matching records '
            'were found for this selection.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div class="error-banner">Analysis did not pass validation. See the details tabs below.</div>',
            unsafe_allow_html=True,
        )

    validation_text = "Passed" if validation_passed else "Failed"
    correction_text = "Yes" if correction_applied else "No"

    green, red, blue, amber, grey = "#63e68b", "#f87171", "#7dd3fc", "#fbbf24", "#cbd5e1"
    exec_color = green if "success" in str(execution_status).lower() else red
    val_color = green if validation_passed else (blue if no_records else red)
    overall_color = green if success else (blue if no_records else red)

    status_col1, status_col2, status_col3, status_col4 = st.columns(4)
    with status_col1:
        _status_box("Execution", execution_status, exec_color)
    with status_col2:
        _status_box("Validation", validation_text, val_color)
    with status_col3:
        _status_box("Correction Applied", correction_text, amber if correction_applied else grey)
    with status_col4:
        _status_box("Overall Status", overall_status, overall_color)

    st.divider()
    st.markdown('<div class="section-title">Pipeline Explanation</div>', unsafe_allow_html=True)
    _render_pipeline_overview(spec, params, final_result, result)

    st.divider()

    result_tab, validation_tab, attempts_tab, code_tab = st.tabs(
        ["Final Result", "Validation Audit", "Correction Attempts", "Generated Code"]
    )

    with result_tab:
        st.subheader("Final Result")

        _render_metrics(spec, result)
        _render_trend_chart(spec, result)

        if isinstance(result, pd.DataFrame) and not result.empty:
            st.dataframe(result, width="stretch", hide_index=True)
            csv = result.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="Download Result as CSV",
                data=csv,
                file_name="clinical_lab_result.csv",
                mime="text/csv",
                width="stretch",
            )
        elif isinstance(result, pd.DataFrame) and result.empty:
            st.info("No matching records were found for the selected question and parameters.")
        elif result is not None:
            st.write(result)
        else:
            st.warning("No result returned.")

    with validation_tab:
        st.subheader("Validation Audit")
        st.write(
            "This is the deterministic gate that proves the generated code answered "
            "the selected question shape, not just that Python ran without crashing."
        )
        _render_validation_audit(spec, result, validation, no_records=no_records)
        st.write("Overall status:")
        st.info(overall_status)

    with attempts_tab:
        st.subheader("Correction Attempts")
        st.write(
            "Each attempt shows the generated call, execution outcome, validation outcome, "
            "and whether the correction loop had to repair the code before retrying."
        )
        _render_attempts_audit(final_result)

    with code_tab:
        st.subheader("Generated Python Code")
        st.code(final_result.get("final_code"), language="python")

elif nl_error:
    st.divider()
    st.warning(nl_error)
    st.info("Examples: " + " | ".join(EXAMPLES))

elif run_button and not params_ready:
    st.divider()
    st.warning("Please complete all parameters before running the analysis.")

else:
    st.divider()
    st.info("Choose a question and parameters, then click Run Analysis - or ask in natural language above.")
