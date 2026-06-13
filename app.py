import streamlit as st
import pandas as pd

import main_pipeline
from main_pipeline import run_pipeline


st.set_page_config(
    page_title="Clinical Lab Analysis System",
    page_icon="🧪",
    layout="wide",
    initial_sidebar_state="collapsed"
)


# =========================
# Custom Styling
# =========================
st.markdown("""
<style>
/* Main page spacing */
.block-container {
    padding-top: 1.5rem;
    padding-bottom: 2rem;
    max-width: 1500px;
}

/* Main title */
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

/* Cards */
.card {
    background-color: #111827;
    border: 1px solid #30363d;
    border-radius: 16px;
    padding: 1.3rem 1.4rem;
    margin-bottom: 1.2rem;
}

.control-card {
    background-color: #111827;
    border: 1px solid #374151;
    border-radius: 18px;
    padding: 1.4rem;
    margin-bottom: 1.5rem;
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

.small-muted {
    color: #9ca3af;
    font-size: 0.95rem;
}

/* Make select boxes easier to read */
div[data-baseweb="select"] > div {
    min-height: 48px;
}

/* Button styling */
.stButton > button {
    height: 48px;
    font-weight: 700;
    border-radius: 12px;
}

/* Dataframes */
[data-testid="stDataFrame"] {
    border-radius: 12px;
}

/* Tabs */
button[data-baseweb="tab"] {
    font-size: 0.95rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)


# =========================
# Load Data
# =========================
merged_data = main_pipeline.merged_data

questions = {
    1: "Show abnormal lab results for a specific admission",
    2: "Return the latest value of a selected lab test during an admission",
    3: "Show the trend of a selected lab test over time during an admission",
    4: "Show all lab tests performed during a specific admission",
    5: "Compare the first and last numeric value of a selected lab test"
}


# =========================
# Header
# =========================
st.markdown('<div class="main-title">Clinical Lab Analysis System</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="subtitle">MIMIC-III based system for predefined clinical laboratory questions</div>',
    unsafe_allow_html=True
)
st.markdown(
    """
    <div class="helper-box">
        This system receives one predefined clinical laboratory question, generates executable Python code,
        runs it on the cleaned MIMIC-III laboratory dataset, validates the output, applies correction when needed,
        and presents the final result clearly.
    </div>
    """,
    unsafe_allow_html=True
)
st.markdown("<br>", unsafe_allow_html=True)

# =========================
# Question Selection Panel
# =========================
st.markdown('<div class="section-title">Question Selection</div>', unsafe_allow_html=True)

question_col, hadm_col = st.columns([2.4, 1])

with question_col:
    question_text = st.selectbox(
        "Choose a clinical question",
        list(questions.values()),
        label_visibility="visible"
    )

question_type = list(questions.keys())[
    list(questions.values()).index(question_text)
]

hadm_ids = sorted(merged_data["HADM_ID"].dropna().unique())
default_hadm = 145834.0 if 145834.0 in hadm_ids else hadm_ids[0]

with hadm_col:
    hadm_id = st.selectbox(
        "Choose Admission ID (HADM_ID)",
        hadm_ids,
        index=hadm_ids.index(default_hadm),
        label_visibility="visible"
    )

params = {"hadm_id": int(hadm_id)}

selected_lab_display = None
selected_row = None

if question_type in [2, 3, 5]:
    available_labs = merged_data[
        merged_data["HADM_ID"] == hadm_id
    ][["ITEMID", "LABEL"]].drop_duplicates()

    available_labs = available_labs.sort_values(by=["LABEL", "ITEMID"])

    available_labs["display"] = (
        available_labs["LABEL"].astype(str)
        + " | ITEMID: "
        + available_labs["ITEMID"].astype(int).astype(str)
    )

    lab_col, run_col = st.columns([2.4, 1])

    with lab_col:
        selected_lab_display = st.selectbox(
            "Choose Lab Test",
            available_labs["display"].tolist()
        )

    selected_row = available_labs[
        available_labs["display"] == selected_lab_display
    ].iloc[0]

    params["itemid"] = int(selected_row["ITEMID"])

    with run_col:
        st.write("")
        st.write("")
        run_button = st.button(
            "Run Analysis",
            type="primary",
            use_container_width=True
        )

else:
    run_col_left, run_col_right = st.columns([2.4, 1])

    with run_col_left:
        st.info("This question only requires an Admission ID.")

    with run_col_right:
        st.write("")
        run_button = st.button(
            "Run Analysis",
            type="primary",
            use_container_width=True
        )



# =========================
# Context Section
# =========================
context_left, context_right = st.columns([1.1, 1])

with context_left:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Selected Question</div>', unsafe_allow_html=True)
    st.info(question_text)

    st.markdown('<div class="section-title">Selected Parameters</div>', unsafe_allow_html=True)
    st.json(params)
    st.markdown('</div>', unsafe_allow_html=True)

with context_right:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Admission Context</div>', unsafe_allow_html=True)

    admission_info = merged_data[
        merged_data["HADM_ID"] == hadm_id
    ][["HADM_ID", "ADMITTIME", "DISCHTIME", "DIAGNOSIS"]].drop_duplicates()

    st.dataframe(
        admission_info,
        use_container_width=True,
        hide_index=True
    )

    if question_type in [2, 3, 5] and selected_row is not None:
        st.markdown('<div class="section-title">Selected Lab Test</div>', unsafe_allow_html=True)
        st.success(
            f"{selected_row['LABEL']}  |  ITEMID: {int(selected_row['ITEMID'])}"
        )

    st.markdown('</div>', unsafe_allow_html=True)


# =========================
# Run Pipeline
# =========================
if run_button:
    st.divider()

    with st.spinner("Running analysis through the full MVP pipeline..."):
        final_result = run_pipeline(question_type, params)

    execution_status = final_result.get("execution", {}).get("status", "Unknown")
    validation_passed = final_result.get("validation", {}).get("valid")
    correction_applied = final_result.get("correction_applied")
    overall_status = final_result.get("status", "Unknown")

    validation_text = "Passed" if validation_passed else "Failed"
    correction_text = "Yes" if correction_applied else "No"

    st.markdown(
        '<div class="success-banner">Analysis completed successfully</div>',
        unsafe_allow_html=True
    )

    status_col1, status_col2, status_col3, status_col4 = st.columns(4)

    with status_col1:
        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-label">Execution</div>
                <div class="status-value">{execution_status}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with status_col2:
        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-label">Validation</div>
                <div class="status-value">{validation_text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with status_col3:
        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-label">Correction Applied</div>
                <div class="status-value">{correction_text}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with status_col4:
        st.markdown(
            f"""
            <div class="status-box">
                <div class="status-label">Overall Status</div>
                <div class="status-value">{overall_status}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

    st.divider()

    result_tab, code_tab, validation_tab, attempts_tab = st.tabs(
        [
            "Final Result",
            "Generated Code",
            "Validation Details",
            "Correction Attempts"
        ]
    )

    with result_tab:
        result = final_result.get("result")

        st.subheader("Final Result")

        if isinstance(result, pd.DataFrame) and not result.empty:
            st.dataframe(
                result,
                use_container_width=True,
                hide_index=True
            )

            csv = result.to_csv(index=False).encode("utf-8")

            st.download_button(
                label="Download Result as CSV",
                data=csv,
                file_name="clinical_lab_result.csv",
                mime="text/csv",
                use_container_width=True
            )

        elif isinstance(result, pd.DataFrame) and result.empty:
            st.warning(
                "No matching records were found for the selected question and parameters."
            )

        elif result is not None:
            st.write(result)

        else:
            st.warning("No result returned.")

    with code_tab:
        st.subheader("Generated Python Code")
        st.code(final_result.get("final_code"), language="python")

    with validation_tab:
        st.subheader("Validation Details")

        validation_message = final_result.get(
            "validation", {}
        ).get("message", "No validation message.")

        if validation_passed:
            st.success(validation_message)
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

else:
    st.divider()
    st.info("Choose a question and parameters, then click Run Analysis.")