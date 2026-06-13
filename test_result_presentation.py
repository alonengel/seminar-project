"""
Smoke test for the console result presentation.

Uses a lightweight stand-in spec so the test does not require the full dataset.
"""

from types import SimpleNamespace

import pandas as pd

from result_presentation import present_result


spec = SimpleNamespace(
    id=2,
    label="Return the latest value of a selected lab test during an admission",
)

params = {"hadm_id": 145834, "itemid": 50893}

generated_code = """
result = get_latest_lab_value(145834, 50893)
"""

sample_result = pd.DataFrame([{
    "HADM_ID": 145834,
    "ITEMID": 50893,
    "LABEL": "Glucose",
    "VALUENUM": 133,
    "VALUEUOM": "mg/dL",
    "CHARTTIME": "2101-10-22 04:00:00",
}])

final_result = {
    "success": True,
    "final_code": generated_code,
    "result": sample_result,
    "execution": {"status": "Execution completed successfully"},
    "validation": {"message": "Validation passed successfully."},
    "correction_applied": False,
    "status": "Execution and validation completed successfully",
}

present_result(
    spec=spec,
    params=params,
    generated_code=generated_code,
    final_result=final_result,
)

print("\ntest_result_presentation: PASSED")
