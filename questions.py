"""
Single source of truth for the supported clinical questions.

Every other module (UI, code generation, validation, pipeline) reads from the
QUESTION_REGISTRY defined here, so adding a new question is a one-place change:
add a QuestionSpec and (if needed) a data-prep function in data_prep.py.

Note: this is "dynamic" only in the developer sense (config-driven). The system
intentionally does NOT accept free-text / user-defined questions at runtime,
which is out of scope per the project guide.
"""

from dataclasses import dataclass
from typing import Callable, List, Optional

import pandas as pd

import data_prep


@dataclass
class QuestionSpec:
    id: int
    label: str
    params: List[str]              # UI widget keys, see PARAM_DEFS
    func: Callable                 # data-prep function in data_prep.py
    expected_columns: List[str]    # columns validation requires in the result
    category: str = "General"      # used to group questions in the UI
    extra_validate: Optional[Callable] = None  # (DataFrame) -> (bool, message)
    chart: Optional[dict] = None   # e.g. {"x": "CHARTTIME", "y": "VALUENUM"}


# ---------------------------------------------------------------------------
# Reusable per-question validators: (result_df) -> (ok: bool, message: str)
# ---------------------------------------------------------------------------
def _only_abnormal(df):
    if "FLAG" in df.columns and not (df["FLAG"] == "abnormal").all():
        return False, "Result should contain only abnormal-flagged rows."
    return True, ""


def _single_row(df):
    if len(df) != 1:
        return False, f"Expected exactly one summary row, got {len(df)}."
    return True, ""


def _time_ascending(df):
    times = pd.to_datetime(df["CHARTTIME"], errors="coerce")
    if not times.is_monotonic_increasing:
        return False, "Results should be ordered by CHARTTIME ascending."
    return True, ""


def _counts_consistent(df):
    cols = {"Abnormal", "Normal", "Total Tests"}
    if cols.issubset(df.columns) and not (df["Abnormal"] + df["Normal"] == df["Total Tests"]).all():
        return False, "Abnormal + Normal must equal Total Tests for every admission."
    return True, ""


# ---------------------------------------------------------------------------
# The registry. IDs 1-5 are unchanged from the original MVP.
# ---------------------------------------------------------------------------
QUESTION_REGISTRY: List[QuestionSpec] = [
    QuestionSpec(
        id=1,
        label="Show abnormal lab results for a specific admission",
        params=["hadm_id"],
        func=data_prep.get_abnormal_results,
        expected_columns=["HADM_ID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME", "FLAG"],
        category="Abnormal results",
        extra_validate=_only_abnormal,
    ),
    QuestionSpec(
        id=2,
        label="Return the latest value of a selected lab test during an admission",
        params=["hadm_id", "itemid"],
        func=data_prep.get_latest_lab_value,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"],
        category="Single lab test",
        extra_validate=_single_row,
    ),
    QuestionSpec(
        id=3,
        label="Show the trend of a selected lab test over time during an admission",
        params=["hadm_id", "itemid"],
        func=data_prep.get_lab_trend,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"],
        category="Single lab test",
        extra_validate=_time_ascending,
        chart={"x": "CHARTTIME", "y": "VALUENUM"},
    ),
    QuestionSpec(
        id=4,
        label="Show all lab tests performed during a specific admission",
        params=["hadm_id"],
        func=data_prep.get_all_lab_tests,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "CHARTTIME"],
        category="Admission overview",
    ),
    QuestionSpec(
        id=5,
        label="Compare the first and last numeric value of a selected lab test",
        params=["hadm_id", "itemid"],
        func=data_prep.compare_first_last_values,
        expected_columns=[
            "HADM_ID", "ITEMID", "LABEL", "First Value", "First Time",
            "Last Value", "Last Time", "VALUEUOM", "Difference",
        ],
        category="Single lab test",
        extra_validate=_single_row,
    ),
    # ----- Step 17 additions -----
    QuestionSpec(
        id=6,
        label="Show summary statistics (min/max/mean) of a lab test during an admission",
        params=["hadm_id", "itemid"],
        func=data_prep.get_lab_summary_stats,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "Count", "Min", "Max", "Mean", "VALUEUOM"],
        category="Single lab test",
        extra_validate=_single_row,
    ),
    QuestionSpec(
        id=7,
        label="Count abnormal vs normal results during an admission",
        params=["hadm_id"],
        func=data_prep.count_abnormal_vs_normal,
        expected_columns=["HADM_ID", "Total Tests", "Abnormal", "Normal"],
        category="Abnormal results",
        extra_validate=_single_row,
    ),
    QuestionSpec(
        id=8,
        label="Show abnormal results for a specific lab test during an admission",
        params=["hadm_id", "itemid"],
        func=data_prep.get_abnormal_results_for_lab,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME", "FLAG"],
        category="Abnormal results",
        extra_validate=_only_abnormal,
    ),
    QuestionSpec(
        id=9,
        label="List all abnormal flagged lab tests during an admission",
        params=["hadm_id"],
        func=data_prep.get_abnormal_tests_summary,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "Abnormal Count"],
        category="Abnormal results",
    ),
    QuestionSpec(
        id=10,
        label="Show lab values within a date range during an admission",
        params=["hadm_id", "itemid", "date_range"],
        func=data_prep.get_lab_values_in_range,
        expected_columns=["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"],
        category="Single lab test",
        extra_validate=_time_ascending,
        chart={"x": "CHARTTIME", "y": "VALUENUM"},
    ),
    QuestionSpec(
        id=11,
        label="List all admissions for a specific patient",
        params=["subject_id"],
        func=data_prep.get_patient_admissions,
        expected_columns=["SUBJECT_ID", "HADM_ID", "ADMITTIME", "DISCHTIME", "DIAGNOSIS"],
        category="Patient overview",
    ),
    QuestionSpec(
        id=12,
        label="Count abnormal vs normal results across all admissions",
        params=[],  # dataset-wide aggregate: no admission/patient/lab input
        func=data_prep.get_abnormal_counts_all_admissions,
        expected_columns=["HADM_ID", "Total Tests", "Abnormal", "Normal"],
        category="Abnormal results",
        extra_validate=_counts_consistent,
    ),
]

REGISTRY_BY_ID = {q.id: q for q in QUESTION_REGISTRY}


def get_question(question_id) -> QuestionSpec:
    spec = REGISTRY_BY_ID.get(question_id)
    if spec is None:
        raise ValueError(f"Unsupported question id: {question_id}")
    return spec


def get_question_by_label(label) -> QuestionSpec:
    for q in QUESTION_REGISTRY:
        if q.label == label:
            return q
    raise ValueError(f"Unknown question label: {label}")


def build_context() -> dict:
    """Maps each data-prep function name to the function, for safe exec()."""
    return {q.func.__name__: q.func for q in QUESTION_REGISTRY}


# ---------------------------------------------------------------------------
# Parameter widget definitions used by the UI.
#   kind  -> which widget to render and how to populate it
#   fills -> the function-argument name(s) the widget produces in `params`
# ---------------------------------------------------------------------------
PARAM_DEFS = {
    "hadm_id":    {"label": "Admission ID (HADM_ID)",  "kind": "hadm",       "fills": ["hadm_id"]},
    "itemid":     {"label": "Lab Test",                "kind": "itemid",     "fills": ["itemid"]},
    "subject_id": {"label": "Patient ID (SUBJECT_ID)", "kind": "subject",    "fills": ["subject_id"]},
    "date_range": {"label": "Date range",              "kind": "date_range", "fills": ["start_time", "end_time"]},
}
