"""
Sandbox for the LLM code-generation agent.

Generated pandas code is checked against an AST allowlist and then executed in a
restricted namespace that exposes only `pd` and the DataFrame `df` plus a small
set of safe builtins. Execution runs in a worker thread with a soft timeout and
the result is row-capped.

This is defense-in-depth: the programmer agent only proposes code, but it can
only ever touch a read-only DataFrame through a small, vetted surface. It never
sees the network, the filesystem, imports, or dangerous builtins. The executor
itself is plain Python (the deterministic "executor agent" in AgentCoder terms).
"""

import ast
import builtins as _builtins
import os
import threading

import pandas as pd

DEFAULT_TIMEOUT = int(os.environ.get("CODEGEN_TIMEOUT_SECONDS", "10"))
DEFAULT_MAX_ROWS = int(os.environ.get("CODEGEN_MAX_ROWS", "5000"))
_MAX_CODE_CHARS = 4000

# Builtins the generated code may use. Anything not listed is unavailable at
# runtime (note the absence of open/eval/exec/__import__/getattr/...).
_SAFE_BUILTIN_NAMES = [
    "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float", "int",
    "len", "list", "map", "max", "min", "range", "round", "set", "sorted",
    "str", "sum", "tuple", "zip",
]
SAFE_BUILTINS = {name: getattr(_builtins, name) for name in _SAFE_BUILTIN_NAMES}

# Expression/statement node types the snippet may contain (allowlist). Loops,
# function/class defs, with/try, imports, etc. are intentionally excluded.
_ALLOWED_NODES = (
    ast.Module, ast.Expr, ast.Assign, ast.AugAssign, ast.AnnAssign,
    ast.Name, ast.Constant, ast.Attribute, ast.Subscript, ast.Slice,
    ast.Tuple, ast.List, ast.Dict, ast.Set,
    ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Call, ast.keyword, ast.Starred,
    ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp, ast.comprehension,
    ast.IfExp, ast.Lambda, ast.arguments, ast.arg,
    ast.JoinedStr, ast.FormattedValue,
)

# Names the snippet may never reference.
_DENY_NAMES = {
    "eval", "exec", "open", "compile", "__import__", "getattr", "setattr",
    "delattr", "globals", "locals", "vars", "input", "exit", "quit",
    "breakpoint", "help", "memoryview", "object", "type", "super",
    "os", "sys", "subprocess", "builtins", "importlib", "io", "pathlib",
    "socket", "shutil", "pickle", "requests",
}

# Attribute/method names that touch the filesystem, network, or an eval engine.
_DENY_ATTRS = {
    "to_csv", "to_pickle", "to_excel", "to_json", "to_parquet", "to_hdf",
    "to_sql", "to_feather", "to_stata", "to_gbq", "to_clipboard",
    "read_csv", "read_pickle", "read_excel", "read_json", "read_parquet",
    "read_sql", "read_table", "read_html", "read_clipboard", "read_fwf",
    "read_stata", "read_hdf", "read_feather",
    "eval", "query", "system", "popen",
}


def check_code(code):
    """Validate a snippet against the allowlist. Returns (ok: bool, reason: str)."""
    if not code or not code.strip():
        return False, "No code was produced."
    if len(code) > _MAX_CODE_CHARS:
        return False, "Generated code is too long."
    try:
        tree = ast.parse(code, mode="exec")
    except SyntaxError as exc:
        return False, f"Syntax error: {exc.msg}"

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            return False, "Imports are not allowed."
        if isinstance(node, (ast.operator, ast.unaryop, ast.cmpop, ast.boolop, ast.expr_context)):
            continue
        if not isinstance(node, _ALLOWED_NODES):
            return False, f"Construct '{type(node).__name__}' is not allowed."
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("_"):
                return False, "Access to private/dunder attributes is not allowed."
            if node.attr in _DENY_ATTRS:
                return False, f"Method '{node.attr}' is not allowed (file/network/eval)."
        if isinstance(node, ast.Name):
            if node.id.startswith("__"):
                return False, "Access to dunder names is not allowed."
            if node.id in _DENY_NAMES:
                return False, f"Use of '{node.id}' is not allowed."
    return True, ""


def run_sandboxed(code, df, timeout=None, max_rows=None):
    """Check, then execute `code` with only {pd, df} + safe builtins available.

    Returns the same dict shape as execution.execute_generated_code:
    {success, result, error, status}.
    """
    timeout = DEFAULT_TIMEOUT if timeout is None else timeout
    max_rows = DEFAULT_MAX_ROWS if max_rows is None else max_rows

    ok, reason = check_code(code)
    if not ok:
        return {"success": False, "result": None, "error": reason, "status": "Blocked by sandbox"}

    namespace = {"__builtins__": SAFE_BUILTINS, "pd": pd, "df": df}
    holder = {}

    def _target():
        try:
            exec(code, namespace)  # noqa: S102 - guarded: AST-checked + restricted builtins
            holder["result"] = namespace.get("result")
            holder["ok"] = True
        except Exception as exc:  # noqa: BLE001 - any runtime error becomes agent feedback
            holder["error"] = f"{type(exc).__name__}: {exc}"
            holder["ok"] = False

    thread = threading.Thread(target=_target, daemon=True)
    thread.start()
    thread.join(timeout)

    if thread.is_alive():
        return {"success": False, "result": None,
                "error": f"Execution exceeded the {timeout}s time limit.", "status": "Timeout"}
    if not holder.get("ok"):
        return {"success": False, "result": None,
                "error": holder.get("error", "Unknown execution error."), "status": "Execution failed"}

    result = holder.get("result")
    if isinstance(result, (pd.DataFrame, pd.Series)) and len(result) > max_rows:
        result = result.head(max_rows)

    return {"success": True, "result": result, "error": None,
            "status": "Execution completed successfully"}
