from execution import execute_generated_code
from validation import validate_result


def correct_generated_code(generated_code, validation_result, execution_result):
    """
    Applies simple rule-based corrections to generated code.

    Parameters:
        generated_code (str): original generated code
        validation_result (dict): validation output
        execution_result (dict): execution output

    Returns:
        str: corrected code
    """

    corrected_code = generated_code

    error_text = ""

    if execution_result.get("error"):
        error_text += execution_result.get("error")

    if validation_result.get("message"):
        error_text += " " + validation_result.get("message")

    if validation_result.get("details"):
        error_text += " " + str(validation_result.get("details"))

    # Correction 1: common typo in function name
    corrected_code = corrected_code.replace(
        "get_lates_lab_value",
        "get_latest_lab_value"
    )

    # Correction 2: common typo in abnormal function
    corrected_code = corrected_code.replace(
        "get_abnormal_result",
        "get_abnormal_results"
    )

    # Correction 3: common typo in trend function
    corrected_code = corrected_code.replace(
        "get_lab_trends",
        "get_lab_trend"
    )

    # Correction 4: common typo in all tests function
    corrected_code = corrected_code.replace(
        "get_all_lab_test",
        "get_all_lab_tests"
    )

    # Correction 5: common typo in comparison function
    corrected_code = corrected_code.replace(
        "compare_first_last_value",
        "compare_first_last_values"
    )

    return corrected_code


def run_with_correction(generated_code, context, question_type, max_attempts=2):
    """
    Executes generated code, validates the result, and applies correction if needed.

    Parameters:
        generated_code (str): generated Python code
        context (dict): available functions/data
        question_type (int): selected question type
        max_attempts (int): maximum correction attempts

    Returns:
        dict: final structured result
    """

    current_code = generated_code
    correction_applied = False
    attempts = []

    for attempt in range(1, max_attempts + 1):
        execution_result = execute_generated_code(current_code, context)
        validation_result = validate_result(question_type, execution_result)

        attempts.append({
            "attempt": attempt,
            "code": current_code,
            "execution": execution_result,
            "validation": validation_result
        })

        if execution_result.get("success") and validation_result.get("valid"):
            return {
                "success": True,
                "final_code": current_code,
                "result": execution_result.get("result"),
                "execution": execution_result,
                "validation": validation_result,
                "correction_applied": correction_applied,
                "attempts": attempts,
                "status": "Execution and validation completed successfully"
            }

        corrected_code = correct_generated_code(
            current_code,
            validation_result,
            execution_result
        )

        if corrected_code == current_code:
            break

        current_code = corrected_code
        correction_applied = True

    return {
        "success": False,
        "final_code": current_code,
        "result": None,
        "execution": execution_result,
        "validation": validation_result,
        "correction_applied": correction_applied,
        "attempts": attempts,
        "status": "Execution or validation failed after correction attempts"
    }