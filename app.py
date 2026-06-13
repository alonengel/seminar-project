import inspect

import pandas as pd
import streamlit as st

import data_prep
import questions
from main_pipeline import run_pipeline


st.set_page_config(
    page_title="Clinical Lab Analysis System",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =========================
# Custom Styling
# =========================
st.markdown("""
<style>
.block-container {
    padding-top: 1.5rem;
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
</style>
""", unsafe_allow_html=True)


merged_data = data_prep.merged_data


# =========================
# Header
# =========================
st.markdown('<div class="main-title">Clinical Lab Analysis System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">MIMIC-III based system for predefined clinical laboratory questions</div>',
    unsafe_allow_html=True,
)
st.markdown(
    f"""
    <div class="helper-box">
        This system takes one predefined clinical laboratory question, generates executable Python code,
        runs it on the cleaned MIMIC-III laboratory dataset, validates the output, applies correction when needed,
        and presents the final result. It currently supports
        <b>{len(questions.QUESTION_REGISTRY)} question types</b>, all defined in a single question registry.
    </div>
    """,
    unsafe_allow_html=True,
)
st.markdown("<br>", unsafe_allow_html=True)


# =========================
# Question Selection Panel
# =========================
st.markdown('<div class="section-title">Question Selection</div>', unsafe_allow_html=True)

categories = ["All"] + sorted({q.category for q in questions.QUESTION_REGISTRY})

cat_col, question_col = st.columns([1, 3])

with cat_col:
    selected_category = st.selectbox("Category", categories)

visible_specs = [
    q for q in questions.QUESTION_REGISTRY
    if selected_category == "All" or q.category == selected_category
]

with question_col:
    question_label = st.selectbox(
        "Choose a clinical question",
        [q.label for q in visible_specs],
    )

spec = questions.get_question_by_label(question_label)


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


# =========================
# Context Section
# =========================
context_left, context_right = st.columns([1.1, 1])

with context_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Question</div>', unsafe_allow_html=True)
    st.info(f"[{spec.id}] {spec.label}")

    st.markdown('<div class="section-title">Selected Parameters</div>', unsafe_allow_html=True)
    st.json(params)
    st.markdown('</div>', unsafe_allow_html=True)

with context_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)

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

    else:
        st.info("Select parameters to see context here.")

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# Run Pipeline
# =========================
if run_button and params_ready:
    st.divider()

    with st.spinner("Running analysis through the full pipeline..."):
        final_result = run_pipeline(spec.id, params)

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

    status_col1, status_col2, status_col3, status_col4 = st.columns(4)

    with status_col1:
        st.markdown(
            f'<div class="status-box"><div class="status-label">Execution</div>'
            f'<div class="status-value">{execution_status}</div></div>',
            unsafe_allow_html=True,
        )
    with status_col2:
        st.markdown(
            f'<div class="status-box"><div class="status-label">Validation</div>'
            f'<div class="status-value">{validation_text}</div></div>',
            unsafe_allow_html=True,
        )
    with status_col3:
        st.markdown(
            f'<div class="status-box"><div class="status-label">Correction Applied</div>'
            f'<div class="status-value">{correction_text}</div></div>',
            unsafe_allow_html=True,
        )
    with status_col4:
        st.markdown(
            f'<div class="status-box"><div class="status-label">Overall Status</div>'
            f'<div class="status-value">{overall_status}</div></div>',
            unsafe_allow_html=True,
        )

    st.divider()

    result_tab, code_tab, validation_tab, attempts_tab = st.tabs(
        ["Final Result", "Generated Code", "Validation Details", "Correction Attempts"]
    )

    with result_tab:
        st.subheader("Final Result")

        if (
            spec.chart
            and isinstance(result, pd.DataFrame)
            and not result.empty
            and spec.chart["x"] in result.columns
            and spec.chart["y"] in result.columns
        ):
            chart_df = (
                result[[spec.chart["x"], spec.chart["y"]]]
                .dropna()
                .set_index(spec.chart["x"])
            )
            if not chart_df.empty:
                st.line_chart(chart_df)

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

    with code_tab:
        st.subheader("Generated Python Code")
        st.code(final_result.get("final_code"), language="python")

    with validation_tab:
        st.subheader("Validation Details")
        if validation_passed:
            st.success(validation_message)
        elif no_records:
            st.info(validation_message)
        else:
            st.error(validation_message)
        st.write("Overall status:")
        st.info(overall_status)

    with attempts_tab:
        st.subheader("Correction Attempts")
        attempts = final_result.get("attempts")
        if attempts:
            st.write(attempts)
        else:
            st.info("No correction attempts were needed.")

elif run_button and not params_ready:
    st.divider()
    st.warning("Please complete all parameters before running the analysis.")

else:
    st.divider()
    st.info("Choose a question and parameters, then click Run Analysis.")
