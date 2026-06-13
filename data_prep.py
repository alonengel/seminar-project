"""
Data preparation layer.

Loads the cleaned MIMIC-III dataset once and exposes one function per
supported clinical question. Each function returns a pandas DataFrame with a
stable set of columns so the validation layer can check it generically.

Keeping the data + functions here (instead of in main_pipeline.py) lets
questions.py import them without creating an import cycle.
"""

import pandas as pd

DATA_PATH = "cleaned_merged_dataset.csv"

merged_data = pd.read_csv(DATA_PATH)
merged_data["CHARTTIME"] = pd.to_datetime(merged_data["CHARTTIME"], errors="coerce")


# ---------------------------------------------------------------------------
# Original 5 questions (IDs 1-5)
# ---------------------------------------------------------------------------
def get_abnormal_results(hadm_id):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["FLAG"] == "abnormal")
    ].sort_values(by="CHARTTIME", ascending=True)

    return result[["HADM_ID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME", "FLAG"]]


def get_latest_lab_value(hadm_id, itemid):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["ITEMID"] == itemid)
    ].sort_values(by="CHARTTIME", ascending=False)

    return result[
        ["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"]
    ].head(1)


def get_lab_trend(hadm_id, itemid):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["ITEMID"] == itemid)
    ].sort_values(by="CHARTTIME", ascending=True)

    return result[["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"]]


def get_all_lab_tests(hadm_id):
    result = merged_data[
        merged_data["HADM_ID"] == hadm_id
    ].sort_values(by="CHARTTIME", ascending=True)

    return result[["HADM_ID", "ITEMID", "LABEL", "CHARTTIME"]]


def compare_first_last_values(hadm_id, itemid):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["ITEMID"] == itemid)
    ].sort_values(by="CHARTTIME", ascending=True)

    if result.empty:
        return pd.DataFrame()

    first = result.iloc[0]
    last = result.iloc[-1]

    return pd.DataFrame([{
        "HADM_ID": hadm_id,
        "ITEMID": itemid,
        "LABEL": first["LABEL"],
        "First Value": first["VALUENUM"],
        "First Time": first["CHARTTIME"],
        "Last Value": last["VALUENUM"],
        "Last Time": last["CHARTTIME"],
        "VALUEUOM": first["VALUEUOM"],
        "Difference": last["VALUENUM"] - first["VALUENUM"],
    }])


# ---------------------------------------------------------------------------
# Step 17 additions (IDs 6-11)
# ---------------------------------------------------------------------------
def get_lab_summary_stats(hadm_id, itemid):
    """Min / max / mean / count of a lab test during an admission."""
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["ITEMID"] == itemid)
    ]

    if result.empty:
        return pd.DataFrame()

    values = result["VALUENUM"]

    return pd.DataFrame([{
        "HADM_ID": hadm_id,
        "ITEMID": itemid,
        "LABEL": result.iloc[0]["LABEL"],
        "Count": int(values.count()),
        "Min": values.min(),
        "Max": values.max(),
        "Mean": round(float(values.mean()), 2) if values.count() else None,
        "VALUEUOM": result.iloc[0]["VALUEUOM"],
    }])


def count_abnormal_vs_normal(hadm_id):
    """One-row summary of how many results were abnormal vs not."""
    result = merged_data[merged_data["HADM_ID"] == hadm_id]

    if result.empty:
        return pd.DataFrame()

    total = len(result)
    abnormal = int((result["FLAG"] == "abnormal").sum())

    return pd.DataFrame([{
        "HADM_ID": hadm_id,
        "Total Tests": total,
        "Abnormal": abnormal,
        "Normal": total - abnormal,
    }])


def get_abnormal_results_for_lab(hadm_id, itemid):
    """Abnormal-flagged readings for one specific lab test in an admission."""
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["ITEMID"] == itemid)
        & (merged_data["FLAG"] == "abnormal")
    ].sort_values(by="CHARTTIME", ascending=True)

    return result[
        ["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME", "FLAG"]
    ]


def get_abnormal_tests_summary(hadm_id):
    """Distinct lab tests that were ever flagged abnormal, with a count each."""
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["FLAG"] == "abnormal")
    ]

    if result.empty:
        return pd.DataFrame(columns=["HADM_ID", "ITEMID", "LABEL", "Abnormal Count"])

    grouped = (
        result.groupby(["ITEMID", "LABEL"])
        .size()
        .reset_index(name="Abnormal Count")
        .sort_values(by="Abnormal Count", ascending=False)
    )
    grouped.insert(0, "HADM_ID", hadm_id)

    return grouped[["HADM_ID", "ITEMID", "LABEL", "Abnormal Count"]]


def get_lab_values_in_range(hadm_id, itemid, start_time, end_time):
    """Readings of one lab test within an inclusive [start, end] date range."""
    start = pd.to_datetime(start_time)
    end = pd.to_datetime(end_time) + pd.Timedelta(days=1)  # make end-day inclusive

    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id)
        & (merged_data["ITEMID"] == itemid)
        & (merged_data["CHARTTIME"] >= start)
        & (merged_data["CHARTTIME"] < end)
    ].sort_values(by="CHARTTIME", ascending=True)

    return result[["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"]]


def get_patient_admissions(subject_id):
    """All distinct admissions for a single patient."""
    result = merged_data[merged_data["SUBJECT_ID_x"] == subject_id]

    if result.empty:
        return pd.DataFrame(
            columns=["SUBJECT_ID", "HADM_ID", "ADMITTIME", "DISCHTIME", "DIAGNOSIS"]
        )

    admissions = (
        result[["SUBJECT_ID_x", "HADM_ID", "ADMITTIME", "DISCHTIME", "DIAGNOSIS"]]
        .drop_duplicates()
        .rename(columns={"SUBJECT_ID_x": "SUBJECT_ID"})
        .sort_values(by="ADMITTIME")
    )

    return admissions[["SUBJECT_ID", "HADM_ID", "ADMITTIME", "DISCHTIME", "DIAGNOSIS"]]
