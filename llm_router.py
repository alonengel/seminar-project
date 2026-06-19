"""
Optional LLM-assisted question routing (controlled).

The model is asked to SELECT exactly one supported question template and extract
its parameters as JSON. The JSON is parsed and validated against the registry
(`question_router.build_route_result`); the model never generates or runs code,
and anything it cannot map to a supported question is rejected. Used only as a
fallback when the rule-based router fails and a provider key is configured.
"""

import json
import re

import llm_client
import question_router as qr
import questions

_SYSTEM = (
    "You translate a clinical lab question into ONE supported question template. "
    "Reply with ONLY a JSON object (no prose, no markdown fences) of the form: "
    '{"question_id": int, "hadm_id": int|null, "lab": string|null, '
    '"subject_id": int|null, "start_time": "YYYY-MM-DD"|null, "end_time": "YYYY-MM-DD"|null}. '
    "Pick question_id from the catalog ONLY IF that template precisely answers the "
    "question. If no template truly fits - for example the user asks for specific "
    "rows, the latest/last N results, a top-N or ranking, or anything the catalog "
    "does not cover - set question_id to 0 instead of forcing an approximate match. "
    "Put the admission number in hadm_id, the patient number in subject_id, the lab "
    "test name in lab, and a date range in start_time/end_time. Use null for anything "
    "not stated. Never invent IDs."
)

_JSON_BLOCK = re.compile(r"\{.*\}", re.DOTALL)


def llm_available():
    return llm_client.available()


def _catalog():
    return "\n".join(
        f"{q.id}: {q.label} (inputs: {', '.join(q.params)})"
        for q in questions.QUESTION_REGISTRY
    )


def _extract_json(text):
    text = (text or "").strip()
    if text.startswith("{"):
        return text
    match = _JSON_BLOCK.search(text)
    if match is None:
        raise ValueError("LLM response did not contain JSON")
    return match.group(0)


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def llm_route_question(text, complete_fn=None):
    """Route a free-text question via the LLM. `complete_fn` is injectable for tests."""
    complete = complete_fn or llm_client.complete
    user = f"Catalog of supported questions:\n{_catalog()}\n\nQuestion: {text}\n\nReturn the JSON now."
    try:
        response = complete(_SYSTEM, user)
        raw = response.text if hasattr(response, "text") else str(response)
        data = json.loads(_extract_json(raw))
    except Exception as exc:  # noqa: BLE001 - degrade gracefully on any LLM/parse error
        return qr._fail(f"LLM interpretation failed ({type(exc).__name__}). Try the dropdown or rephrase.")

    qid = _to_int(data.get("question_id"))
    if not qid:  # 0/null -> the model judged that no template fits
        return qr._fail(
            "No ready-made question matches this request. "
            "Try 'Advanced: AI writes code', or rephrase to one of the supported questions."
        )

    hadm_id = _to_int(data.get("hadm_id"))
    subject_id = _to_int(data.get("subject_id"))
    lab = data.get("lab")
    dates = [d for d in (data.get("start_time"), data.get("end_time")) if d]

    itemid, lab_label = (None, None)
    if lab and hadm_id is not None:
        itemid, lab_label = qr._resolve_lab(str(lab).lower(), hadm_id)
        if lab_label is None:
            lab_label = str(lab)

    return qr.build_route_result(
        qid,
        hadm_id=hadm_id,
        subject_id=subject_id,
        itemid=itemid,
        lab_label=lab_label,
        dates=dates,
        method="LLM",
    )
