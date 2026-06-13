import pandas as pd
from correction import run_with_correction


def get_latest_lab_value(hadm_id, itemid):
    return pd.DataFrame([
        {
            "HADM_ID": hadm_id,
            "ITEMID": itemid,
            "LABEL": "Glucose",
            "VALUENUM": 133,
            "VALUEUOM": "mg/dL",
            "CHARTTIME": "2101-10-22 04:00:00"
        }
    ])


# Intentionally wrong function name: get_lates_lab_value
generated_code = """
result = get_lates_lab_value(145834, 50893)
"""

context = {
    "get_latest_lab_value": get_latest_lab_value
}

final_result = run_with_correction(
    generated_code=generated_code,
    context=context,
    question_type=2,
    max_attempts=2
)

print(final_result)