import pandas as pd


EXPECTED_COLUMNS = {
    1: ["HADM_ID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME", "FLAG"],
    2: ["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"],
    3: ["HADM_ID", "ITEMID", "LABEL", "VALUENUM", "VALUEUOM", "CHARTTIME"],
    4: ["HADM_ID", "ITEMID", "LABEL", "CHARTTIME"],
    5: ["HADM_ID", "ITEMID", "LABEL", "First Value", "First Time", "Last Value", "Last Time", "VALUEUOM", "Difference"]
}


def validate_result(question_type, execution_result):
    """
    Validates whether the generated code produced the expected output.

    Parameters:
        question_type (int): selected question number
        execution_result (dict): result returned from execute_generated_code()

    Returns:
        dict: validation status and details
    """

    if not execution_result.get("success"):
        return {
            "valid": False,
            "message": "Execution failed, so validation cannot pass.",
            "details": execution_result.get("error")
        }

    result = execution_result.get("result")

    if result is None:
        return {
            "valid": False,
            "message": "No result object was returned.",
            "details": None
        }

    if isinstance(result, str):
        if result.strip() == "":
            return {
                "valid": False,
                "message": "Result is an empty string.",
                "details": None
            }

        return {
            "valid": True,
            "message": "String result returned successfully.",
            "details": result
        }

    if not isinstance(result, pd.DataFrame):
        return {
            "valid": False,
            "message": "Result is not a pandas DataFrame.",
            "details": str(type(result))
        }

    expected_cols = EXPECTED_COLUMNS.get(question_type)

    if expected_cols is None:
        return {
            "valid": False,
            "message": "Unsupported question type for validation.",
            "details": question_type
        }

    missing_cols = [col for col in expected_cols if col not in result.columns]

    if missing_cols:
        return {
            "valid": False,
            "message": "Result is missing expected columns.",
            "details": missing_cols
        }

    if result.empty:
        return {
            "valid": False,
            "message": "Result DataFrame is empty.",
            "details": None
        }

    if question_type == 1:
        if "FLAG" in result.columns and not all(result["FLAG"] == "abnormal"):
            return {
                "valid": False,
                "message": "Question 1 should return only abnormal results.",
                "details": "Some rows are not marked as abnormal."
            }

    if question_type == 2:
        if len(result) != 1:
            return {
                "valid": False,
                "message": "Question 2 should return exactly one latest record.",
                "details": f"Returned rows: {len(result)}"
            }

    if question_type == 3:
        times = pd.to_datetime(result["CHARTTIME"], errors="coerce")
        if not times.is_monotonic_increasing:
            return {
                "valid": False,
                "message": "Question 3 trend results should be ordered by CHARTTIME ascending.",
                "details": None
            }

    if question_type == 5:
        if len(result) != 1:
            return {
                "valid": False,
                "message": "Question 5 should return one comparison summary row.",
                "details": f"Returned rows: {len(result)}"
            }

    return {
        "valid": True,
        "message": "Validation passed successfully.",
        "details": None
    }

