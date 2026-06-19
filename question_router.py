"""
Controlled natural-language question router.

Maps a free-text clinical lab question to exactly ONE of the supported question
templates (by id) and extracts its parameters. It can only route to the
predefined questions in the registry and never generates free-form code.

`route_question` is rule-based / keyword matching. `smart_route` tries the rules
first and, if they cannot match and an LLM provider is configured, falls back to
the optional LLM-assisted router (`llm_router.py`). Both share
`build_route_result` so validation is identical.
"""

import inspect
import re

import data_prep
import questions

EXAMPLES = [
    "Show abnormal lab results for admission 145834",
    "What is the latest chloride value for admission 199884?",
    "Show hematocrit trend for admission 107521",
    "Compare first and last pO2 values for admission 177047",
]

# Valid identifier sets, for fast existence checks and clear error messages.
_HADM_IDS = set(data_prep.merged_data["HADM_ID"].dropna().astype(int))
_SUBJECT_IDS = set(data_prep.merged_data["SUBJECT_ID_x"].dropna().astype(int))


def _fail(message):
    return {"matched": False, "question_id": None, "params": {}, "lab_label": None, "message": message}


def _search_int(text, patterns):
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return int(match.group(1))
    return None


def _extract_hadm(text):
    return _search_int(text, [r"admission\s+(?:id\s+)?#?(\d{3,})", r"hadm[_ ]?id?\s*#?(\d{3,})"])


def _extract_subject(text):
    return _search_int(text, [r"patient\s+(?:id\s+)?#?(\d+)", r"subject\s+(?:id\s+)?#?(\d+)"])


def _resolve_lab(text, hadm_id):
    """Resolve a lab name in the text to an ITEMID available in the admission."""
    if hadm_id is None:
        return None, None
    subset = data_prep.merged_data[data_prep.merged_data["HADM_ID"] == hadm_id]
    if subset.empty:
        return None, None
    pairs = (
        subset.groupby(["ITEMID", "LABEL"]).size()
        .reset_index(name="n").sort_values("n", ascending=False)
    )
    for _, row in pairs.iterrows():
        if str(row["LABEL"]).lower() in text:
            return int(row["ITEMID"]), str(row["LABEL"])
    for _, row in pairs.iterrows():
        token = re.split(r"[ ,]+", str(row["LABEL"]).lower())[0]
        if len(token) >= 3 and re.search(rf"\b{re.escape(token)}\b", text):
            return int(row["ITEMID"]), str(row["LABEL"])
    return None, None


def _has(text, *phrases):
    return any(phrase in text for phrase in phrases)


def _has_word(text, *words):
    return bool(re.search(r"\b(" + "|".join(map(re.escape, words)) + r")\b", text))


def _classify(text, has_lab):
    if _has_word(text, "patient", "subject") and "admission" in text and _has(text, "all", "list", "every"):
        return 11
    if _has(text, "date range", "between") and len(re.findall(r"\d{4}-\d{2}-\d{2}", text)) >= 2:
        return 10
    if _has(text, "compare") or (_has(text, "first") and _has(text, "last")):
        return 5
    if _has(text, "trend", "over time", "time series"):
        return 3
    if _has(text, "latest", "most recent", "last value", "current value"):
        return 2
    if _has_word(text, "summary", "statistics", "statistic", "average", "mean", "minimum", "maximum", "min", "max"):
        return 6
    if _has(text, "abnormal"):
        if _has(text, "all admission", "all the admission", "every admission", "across admission", "each admission"):
            return 12
        if _has(text, "count", "how many", "number of", "vs normal", "versus normal", "normal vs"):
            return 7
        if _has(text, "which test", "what test", "list", "distinct"):
            return 9
        return 8 if has_lab else 1
    if _has(text, "all lab tests", "all tests", "every test", "list tests"):
        return 4
    return None


def build_route_result(question_id, *, hadm_id=None, subject_id=None, itemid=None,
                       lab_label=None, dates=None, method="rules"):
    """Validate extracted entities against the registry and build the result dict.

    Shared by the rule-based router and the LLM router so both enforce the same
    rules: known admission/patient IDs, a supported question, and the required
    parameters for that question.
    """
    if hadm_id is not None and hadm_id not in _HADM_IDS:
        return _fail(f"Admission {hadm_id} was not found in the dataset.")
    if subject_id is not None and subject_id not in _SUBJECT_IDS:
        return _fail(f"Patient {subject_id} was not found in the dataset.")

    if question_id is None:
        return _fail("Could not recognise the question. Try wording it like the examples, or use the dropdown above.")
    try:
        spec = questions.get_question(int(question_id))
    except (ValueError, TypeError):
        return _fail(f"Unsupported question id: {question_id}.")

    needs = set(inspect.signature(spec.func).parameters)
    params = {}

    if "hadm_id" in needs:
        if hadm_id is None:
            return _fail(
                "This question is answered per-admission - please name an admission ID "
                "(e.g. 'admission 145834'). For a dataset-wide view, ask for "
                "'abnormal results across all admissions'."
            )
        params["hadm_id"] = hadm_id
    if "subject_id" in needs:
        if subject_id is None:
            return _fail("Please include a patient ID, for example 'patient 3'.")
        params["subject_id"] = subject_id
    if "itemid" in needs:
        if itemid is None:
            return _fail(
                f"Could not find a lab test for admission {hadm_id}. "
                "Try naming one like chloride, hematocrit, or pO2."
            )
        params["itemid"] = itemid
    if "start_time" in needs or "end_time" in needs:
        if not dates or len(dates) < 2:
            return _fail("Please include a start and end date (YYYY-MM-DD).")
        params["start_time"], params["end_time"] = dates[0], dates[1]

    detail = []
    if "hadm_id" in params:
        detail.append(f"admission {params['hadm_id']}")
    if "subject_id" in params:
        detail.append(f"patient {params['subject_id']}")
    if lab_label and "itemid" in params:
        detail.append(f"lab {lab_label} (ITEMID {params['itemid']})")
    message = f"[{spec.id}] {spec.label}" + (" | " + ", ".join(detail) if detail else "")

    return {
        "matched": True,
        "question_id": spec.id,
        "params": params,
        "lab_label": lab_label,
        "message": message,
        "method": method,
    }


def route_question(text):
    """Rule-based routing. Returns {matched, question_id, params, lab_label, message, method}."""
    cleaned = (text or "").lower().strip()
    if not cleaned:
        return _fail("Please type a question.")

    hadm_id = _extract_hadm(cleaned)
    subject_id = _extract_subject(cleaned)
    itemid, lab_label = _resolve_lab(cleaned, hadm_id)
    question_id = _classify(cleaned, has_lab=itemid is not None)
    dates = re.findall(r"\d{4}-\d{2}-\d{2}", cleaned)

    return build_route_result(
        question_id, hadm_id=hadm_id, subject_id=subject_id,
        itemid=itemid, lab_label=lab_label, dates=dates, method="rules",
    )


def smart_route(text):
    """Rule-based routing first; fall back to the LLM router only if the rules
    cannot match and a provider key is configured. Always controlled to the
    supported templates."""
    result = route_question(text)
    if result["matched"] or not (text or "").strip():
        return result
    try:
        import llm_router
    except Exception:
        return result
    if not llm_router.llm_available():
        return result
    llm_result = llm_router.llm_route_question(text)
    if llm_result["matched"]:
        return llm_result
    # Both failed: prefer the LLM's specific reason, unless the LLM call errored.
    if "LLM interpretation failed" in llm_result.get("message", ""):
        return result
    return llm_result


def route(text, mode="auto"):
    """Dispatch routing by mode: 'rules' (no LLM), 'llm' (always LLM),
    'auto' (rules first, LLM fallback), or 'codegen' (guarded LLM code generation).

    Note: 'codegen' returns the agent-pipeline result shape (success/result/...),
    not a routing dict; it is used only by the experimental UI mode.
    """
    if mode == "rules":
        return route_question(text)
    if mode == "codegen":
        from agent_pipeline import run_codegen
        return run_codegen(text)
    if mode == "llm":
        try:
            import llm_router
        except Exception:
            return _fail("The LLM router is unavailable.")
        if not llm_router.llm_available():
            return _fail("LLM is not configured. Set an API key in .env, or use Rules mode.")
        return llm_router.llm_route_question(text)
    return smart_route(text)
