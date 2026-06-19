"""
Orchestrator for the guarded LLM code-generation pipeline (AgentCoder-style).

Loop: the programmer agent writes code -> the sandbox executor runs it -> the
deterministic validator gates the result -> on failure the error is fed back and
the programmer retries, up to a small budget. This mirrors the structure of
correction.run_with_correction (and returns the same result shape) so the
Streamlit UI renders it with the existing result/code/validation tabs. We keep
the orchestration in-repo and lightweight rather than pulling in CrewAI/AutoGen.
"""

import os

import code_agent
import sandbox
import validation

DEFAULT_MAX_ATTEMPTS = int(os.environ.get("CODEGEN_MAX_ATTEMPTS", "3"))


def _failure(message, final_code="", attempts=None, execution=None, validation_result=None, plan=""):
    return {
        "success": False,
        "final_code": final_code,
        "plan": plan,
        "result": None,
        "execution": execution or {},
        "validation": validation_result or {"valid": False, "message": message, "details": None},
        "correction_applied": bool(attempts and len(attempts) > 1),
        "attempts": attempts or [],
        "method": "LLM code-gen",
        "status": message,
    }


def run_codegen(question, df=None, max_attempts=None, complete_fn=None, timeout=None, max_rows=None):
    """Generate, sandbox-execute, and validate pandas code for a free-text question."""
    if not (question or "").strip():
        return _failure("Please type a question.")

    if df is None:
        import data_prep
        df = data_prep.merged_data.copy(deep=False)

    max_attempts = DEFAULT_MAX_ATTEMPTS if max_attempts is None else max_attempts
    schema_text, sample = code_agent.build_schema(df)

    attempts = []
    feedback = None
    final_code = ""
    plan = ""
    execution_result = {}
    validation_result = {}

    for attempt in range(1, max_attempts + 1):
        try:
            code = code_agent.generate_analysis_code(
                question, schema_text, sample=sample, feedback=feedback, complete_fn=complete_fn
            )
        except Exception as exc:  # noqa: BLE001 - LLM/transport errors degrade gracefully
            return _failure(
                f"LLM code generation failed ({type(exc).__name__}).",
                final_code=final_code, attempts=attempts, plan=plan,
            )

        final_code = code
        plan = code_agent.extract_plan(code)
        execution_result = sandbox.run_sandboxed(code, df, timeout=timeout, max_rows=max_rows)

        if execution_result.get("success"):
            validation_result = validation.validate_freeform_result(
                execution_result.get("result"), max_rows=max_rows
            )
        else:
            validation_result = {
                "valid": False,
                "message": execution_result.get("error", "Execution failed."),
                "details": execution_result.get("status"),
            }

        attempts.append({
            "attempt": attempt,
            "code": code,
            "execution": execution_result,
            "validation": validation_result,
        })

        if execution_result.get("success") and validation_result.get("valid"):
            return {
                "success": True,
                "final_code": code,
                "plan": plan,
                "result": execution_result.get("result"),
                "execution": execution_result,
                "validation": validation_result,
                "correction_applied": attempt > 1,
                "attempts": attempts,
                "method": "LLM code-gen",
                "status": "Code generation and validation completed successfully",
            }

        feedback = (
            f"Status: {execution_result.get('status')}. "
            f"Error: {execution_result.get('error')}. "
            f"Validation: {validation_result.get('message')}"
        )

    return _failure(
        "Could not produce a valid result after several attempts.",
        final_code=final_code, attempts=attempts, execution=execution_result,
        validation_result=validation_result, plan=plan,
    )
