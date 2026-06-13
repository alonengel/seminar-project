from execution import execute_generated_code


def generate_code(question_type, params):
    hadm_id = params.get("hadm_id")
    itemid = params.get("itemid")

    if question_type == 1:
        return f"""
result = get_abnormal_results({hadm_id})
"""

    elif question_type == 2:
        return f"""
result = get_latest_lab_value({hadm_id}, {itemid})
"""

    elif question_type == 3:
        return f"""
result = get_lab_trend({hadm_id}, {itemid})
"""

    elif question_type == 4:
        return f"""
result = get_all_lab_tests({hadm_id})
"""

    elif question_type == 5:
        return f"""
result = compare_first_last_values({hadm_id}, {itemid})
"""

    else:
        raise ValueError("Unsupported question type")


# Mock functions for testing Step 10
def get_abnormal_results(hadm_id):
    return f"Mock abnormal results for HADM_ID={hadm_id}"


def get_latest_lab_value(hadm_id, itemid):
    return f"Mock latest lab value for HADM_ID={hadm_id}, ITEMID={itemid}"


def get_lab_trend(hadm_id, itemid):
    return f"Mock lab trend for HADM_ID={hadm_id}, ITEMID={itemid}"


def get_all_lab_tests(hadm_id):
    return f"Mock all lab tests for HADM_ID={hadm_id}"


def compare_first_last_values(hadm_id, itemid):
    return f"Mock first-last comparison for HADM_ID={hadm_id}, ITEMID={itemid}"


# Test
if __name__ == "__main__":
    params = {
        "hadm_id": 145834,
        "itemid": 50893
    }

    code = generate_code(2, params)

    print("Generated Code:")
    print(code)

    context = {
        "get_abnormal_results": get_abnormal_results,
        "get_latest_lab_value": get_latest_lab_value,
        "get_lab_trend": get_lab_trend,
        "get_all_lab_tests": get_all_lab_tests,
        "compare_first_last_values": compare_first_last_values
    }

    execution_result = execute_generated_code(code, context)

    print("\nExecution Result:")
    print(execution_result)