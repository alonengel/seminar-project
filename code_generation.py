"""
Code generation module.

Builds an executable Python snippet for a question from its QuestionSpec.
The function arguments are read from the data-prep function's own signature,
so a new question needs no changes here - only a new QuestionSpec.
"""

import inspect


def generate_code(spec, params):
    """
    Returns a code string like:  result = get_latest_lab_value(199884, 50902)

    Parameters:
        spec: a questions.QuestionSpec
        params (dict): values keyed by the data-prep function's argument names
    """
    func_name = spec.func.__name__
    arg_names = list(inspect.signature(spec.func).parameters.keys())

    missing = [name for name in arg_names if name not in params]
    if missing:
        raise KeyError(
            f"Missing parameter(s) {missing} for question {spec.id} ({func_name})"
        )

    arg_str = ", ".join(repr(params[name]) for name in arg_names)
    return f"\nresult = {func_name}({arg_str})\n"
