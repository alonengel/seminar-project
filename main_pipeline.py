"""
End-to-end pipeline.

Wires the registry-driven modules together:
    question id -> generate code -> execute + validate (+ correct) -> present.
"""

import data_prep
import questions
from code_generation import generate_code
from correction import run_with_correction
from result_presentation import present_result


# Re-exported for the UI and any callers that expect main_pipeline.merged_data.
merged_data = data_prep.merged_data

# Functions available to the generated code, built automatically from the registry.
context = questions.build_context()


def run_pipeline(question_type, params):
    spec = questions.get_question(question_type)

    generated_code = generate_code(spec, params)

    final_result = run_with_correction(
        generated_code=generated_code,
        context=context,
        spec=spec,
        max_attempts=2,
    )

    present_result(
        spec=spec,
        params=params,
        generated_code=final_result.get("final_code"),
        final_result=final_result,
    )

    return final_result


if __name__ == "__main__":
    run_pipeline(question_type=2, params={"hadm_id": 145834, "itemid": 50893})
