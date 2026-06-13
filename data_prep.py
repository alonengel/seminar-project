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
