"""
Smoke test for the correction loop.

Uses a lightweight stand-in spec (SimpleNamespace) and a mock data function so
the test does not require the full MIMIC-III dataset to be present.
"""

from types import SimpleNamespace

import pandas as pd

from correction import run_with_correction


def get_latest_lab_value(hadm_id, itemid):
    return pd.DataFrame([{
        "HADM_ID": hadm_id,
        "ITEMID": itemid,
        "LABEL": "Glucose",
        "VALUENUM": 133,
        "VALUEUOM": "mg/dL",
        "CHARTTIME": "2101-10-22 04:00:00",
    }])


# Lightweight stand-in for questions.QuestionSpec (only the fields the
# correction/validation path reads).
spec = SimpleNamespace(
    id=2,
    label="Return the latest value of a selected lab test during an admission",
    expected_columns=["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"],
    extra_validate=lambda df: (len(df) == 1, "Expected exactly one row."),
)

# Intentionally wrong function name (get_lates_lab_value) to trigger correction.
generated_code = """
result = get_lates_lab_value(145834, 50893)
"""

context = {"get_latest_lab_value": get_latest_lab_value}

final_result = run_with_correction(
    generated_code=generated_code,
    context=context,
    spec=spec,
    max_attempts=2,
)

print("success:", final_result["success"])
print("correction_applied:", final_result["correction_applied"])
print("final_code:", final_result["final_code"].strip())
print("validation:", final_result["validation"]["message"])

assert final_result["success"], "Correction loop should fix the typo and succeed"
assert final_result["correction_applied"], "Correction should have been applied"
print("\ntest_correction: PASSED")
