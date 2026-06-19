"""
Correction module (simplified Self-Edit).

Runs the generated code, validates it against the question spec, and applies
simple rule-based fixes (e.g. common function-name typos) before retrying, up
to a small number of attempts.
"""

import re

from execution import execute_generated_code
from validation import validate_result

# Known function-name typos a flakier generator might emit, and their fixes.
# Matched on whole identifiers (word boundaries) so a wrong name that is a prefix
# of a valid one - e.g. "get_abnormal_result" inside "get_abnormal_results_for_lab"
# - is not accidentally rewritten.
TYPO_FIXES = {
    "get_lates_lab_value": "get_latest_lab_value",
    "get_abnormal_result": "get_abnormal_results",
    "get_lab_trends": "get_lab_trend",
    "get_all_lab_test": "get_all_lab_tests",
    "compare_first_last_value": "compare_first_last_values",
}

# Correct name -> a typo of it; used by the UI "inject a typo" demo to force a
# first-attempt failure that the correction loop then repairs.
REVERSE_TYPOS = {right: wrong for wrong, right in TYPO_FIXES.items()}


def correct_generated_code(generated_code, validation_result, execution_result):
    """Applies simple rule-based corrections to generated code."""
    corrected_code = generated_code

    error_text = ""
    if execution_result.get("error"):
        error_text += execution_result.get("error")
    if validation_result.get("message"):
        error_text += " " + validation_result.get("message")
    if validation_result.get("details"):
        error_text += " " + str(validation_result.get("details"))

    for wrong, right in TYPO_FIXES.items():
        corrected_code = re.sub(rf"\b{re.escape(wrong)}\b", right, corrected_code)

    return corrected_code


def run_with_correction(generated_code, context, spec, max_attempts=2):
    """
    Executes generated code, validates the result, and applies correction if
    needed.

    Parameters:
        generated_code (str): generated Python code
        context (dict): available functions/data for exec()
        spec: a questions.QuestionSpec
        max_attempts (int): maximum correction attempts

    Returns:
        dict: final structured result
    """
    current_code = generated_code
    correction_applied = False
    attempts = []

    execution_result = {}
    validation_result = {}

    for attempt in range(1, max_attempts + 1):
        execution_result = execute_generated_code(current_code, context)
        validation_result = validate_result(spec, execution_result)

        attempts.append({
            "attempt": attempt,
            "code": current_code,
            "execution": execution_result,
            "validation": validation_result,
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
                "status": "Execution and validation completed successfully",
            }

        corrected_code = correct_generated_code(
            current_code, validation_result, execution_result
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
        "status": "Execution or validation failed after correction attempts",
    }
