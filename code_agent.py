"""
Programmer agent for the LLM code-generation pipeline (AgentCoder's role #1).

Given a natural-language question and the dataset schema, it asks the LLM to
write ONE pandas snippet that assigns the answer to `result`, using only the
in-scope DataFrame `df` and `pd`. On a retry it receives the previous
error/validation feedback and refines the code. The model never executes
anything - the sandbox + validator do. `complete_fn` is injectable so tests
run fully offline.
"""

import os
import re

import llm_client

_CODEGEN_MAX_TOKENS = int(os.environ.get("CODEGEN_MAX_TOKENS", "1500"))

_SYSTEM = (
    "You are a careful clinical-data analyst. Write a SINGLE Python snippet that "
    "uses pandas to answer a question about a lab-results DataFrame.\n"
    "Strict rules:\n"
    "- Use ONLY the provided DataFrame `df` and the `pd` module.\n"
    "- Assign the final answer to a variable named `result` (a DataFrame, Series, or scalar).\n"
    "- Do NOT import anything, read or write files, or use input/eval/exec/query.\n"
    "- Do NOT access private/underscore attributes and do NOT use loops; prefer vectorized pandas.\n"
    "- You may add one short '# plan: ...' comment, then the code. Output code only, no prose."
)

_FENCE = re.compile(r"```(?:python)?\s*(.*?)```", re.DOTALL)


def build_schema(df, sample_rows=3):
    """Return (schema_text, sample_records) describing the DataFrame for the prompt."""
    columns = ", ".join(f"{col} ({df[col].dtype})" for col in df.columns)
    try:
        sample = df.head(sample_rows).to_dict("records")
    except Exception:  # noqa: BLE001 - sampling is best-effort prompt context only
        sample = []
    return f"Columns: {columns}", sample


def extract_code(text):
    """Pull the code out of an LLM reply (strips a markdown fence if present)."""
    text = (text or "").strip()
    match = _FENCE.search(text)
    return match.group(1).strip() if match else text


def extract_plan(code):
    """Collect leading '# ...' comment lines into a short human-readable plan."""
    lines = [ln.strip()[1:].strip() for ln in code.splitlines() if ln.strip().startswith("#")]
    return " ".join(lines).strip()[:300]


def build_prompt(question, schema_text, sample=None, feedback=None):
    parts = [f"DataFrame schema:\n{schema_text}"]
    if sample:
        parts.append(f"Sample rows: {sample}")
    parts.append(f"Question: {question}")
    if feedback:
        parts.append(f"Your previous attempt failed. Fix it.\nFeedback: {feedback}")
    parts.append("Return the code now.")
    return "\n\n".join(parts)


def generate_analysis_code(question, schema_text, sample=None, feedback=None, complete_fn=None):
    """Ask the programmer agent for a pandas snippet. Returns the code string."""
    complete = complete_fn or llm_client.complete
    user = build_prompt(question, schema_text, sample=sample, feedback=feedback)
    response = complete(_SYSTEM, user, max_tokens=_CODEGEN_MAX_TOKENS)
    raw = response.text if hasattr(response, "text") else str(response)
    return extract_code(raw)
