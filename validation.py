"""
Validation module.

Generic checks (execution succeeded, result is a non-empty DataFrame with the
expected columns) plus an optional per-question rule supplied by the
QuestionSpec (spec.extra_validate). No per-id branching lives here anymore.
"""

import pandas as pd


def validate_result(spec, execution_result):
    """
    Parameters:
        spec: a questions.QuestionSpec
        execution_result (dict): output of execute_generated_code()

    Returns:
        dict with keys: valid (bool), message (str), details
    """
    if not execution_result.get("success"):
        return {
            "valid": False,
            "message": "Execution failed, so validation cannot pass.",
            "details": execution_result.get("error"),
        }

    result = execution_result.get("result")

    if result is None:
        return {
            "valid": False,
            "message": "No result object was returned.",
            "details": None,
        }

    if isinstance(result, str):
        if result.strip() == "":
            return {"valid": False, "message": "Result is an empty string.", "details": None}
        return {"valid": True, "message": "String result returned successfully.", "details": result}

    if not isinstance(result, pd.DataFrame):
        return {
            "valid": False,
            "message": "Result is not a pandas DataFrame.",
            "details": str(type(result)),
        }

    missing_cols = [col for col in spec.expected_columns if col not in result.columns]
    if missing_cols:
        return {
            "valid": False,
            "message": "Result is missing expected columns.",
            "details": missing_cols,
        }

    if result.empty:
        return {"valid": False, "message": "Result DataFrame is empty.", "details": None}

    if spec.extra_validate is not None:
        ok, message = spec.extra_validate(result)
        if not ok:
            return {"valid": False, "message": message, "details": None}

    return {"valid": True, "message": "Validation passed successfully.", "details": None}
