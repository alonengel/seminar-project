import pandas as pd

from code_generation import generate_code
from correction import run_with_correction
from result_presentation import present_result


# -----------------------------
# Load cleaned dataset
# -----------------------------
merged_data = pd.read_csv("cleaned_merged_dataset.csv")
merged_data["CHARTTIME"] = pd.to_datetime(merged_data["CHARTTIME"], errors="coerce")


# -----------------------------
# Real Data Preparation Functions
# -----------------------------
def get_abnormal_results(hadm_id):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id) &
        (merged_data["FLAG"] == "abnormal")
    ]

    return result[
        ["HADM_ID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME", "FLAG"]
    ]


def get_latest_lab_value(hadm_id, itemid):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id) &
        (merged_data["ITEMID"] == itemid)
    ].sort_values(by="CHARTTIME", ascending=False)

    return result[
        ["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"]
    ].head(1)


def get_lab_trend(hadm_id, itemid):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id) &
        (merged_data["ITEMID"] == itemid)
    ].sort_values(by="CHARTTIME", ascending=True)

    return result[
        ["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"]
    ]


def get_all_lab_tests(hadm_id):
    result = merged_data[
        merged_data["HADM_ID"] == hadm_id
    ].sort_values(by="CHARTTIME", ascending=True)

    return result[
        ["HADM_ID", "ITEMID", "LABEL", "CHARTTIME"]
    ]


def compare_first_last_values(hadm_id, itemid):
    result = merged_data[
        (merged_data["HADM_ID"] == hadm_id) &
        (merged_data["ITEMID"] == itemid)
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
        "Difference": last["VALUENUM"] - first["VALUENUM"]
    }])


# -----------------------------
# Context for generated code
# -----------------------------
context = {
    "get_abnormal_results": get_abnormal_results,
    "get_latest_lab_value": get_latest_lab_value,
    "get_lab_trend": get_lab_trend,
    "get_all_lab_tests": get_all_lab_tests,
    "compare_first_last_values": compare_first_last_values
}


# -----------------------------
# Full End-to-End Pipeline
# -----------------------------
def run_pipeline(question_type, params):
    generated_code = generate_code(question_type, params)

    final_result = run_with_correction(
        generated_code=generated_code,
        context=context,
        question_type=question_type,
        max_attempts=2
    )

    present_result(
        question_type=question_type,
        params=params,
        generated_code=final_result.get("final_code"),
        final_result=final_result
    )

    return final_result


# -----------------------------
# Test the full MVP pipeline
# -----------------------------
if __name__ == "__main__":
    params = {
        "hadm_id": 145834,
        "itemid": 50893
    }

    run_pipeline(
        question_type=2,
        params=params
    )