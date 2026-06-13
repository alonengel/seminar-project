def execute_generated_code(generated_code, context):
    local_context = context.copy()

    try:
        exec(generated_code, {}, local_context)

        result = local_context.get("result", None)

        return {
            "success": True,
            "result": result,
            "error": None,
            "status": "Execution completed successfully"
        }

    except Exception as e:
        return {
            "success": False,
            "result": None,
            "error": str(e),
            "status": "Execution failed"
        }