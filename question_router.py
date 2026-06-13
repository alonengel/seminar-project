"""
Controlled natural-language question router.

Maps a free-text clinical lab question to exactly ONE of the supported question
templates (by id) and extracts its parameters. This is deliberately rule-based /
keyword matching: it never generates free-form code, and it can only route to
the predefined questions in the registry. A full LLM-based natural-language
interface is proposed as future work.
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
        if _has(text, "count", "how many", "number of", "vs normal", "versus normal", "normal vs"):
            return 7
        if _has(text, "which test", "what test", "list", "distinct"):
            return 9
        return 8 if has_lab else 1
    if _has(text, "all lab tests", "all tests", "every test", "list tests"):
        return 4
    return None


def route_question(text):
    """Return {matched, question_id, params, lab_label, message}."""
    cleaned = (text or "").lower().strip()
    if not cleaned:
        return _fail("Please type a question.")

    hadm_id = _extract_hadm(cleaned)
    subject_id = _extract_subject(cleaned)

    if hadm_id is not None and hadm_id not in _HADM_IDS:
        return _fail(f"Admission {hadm_id} was not found in the dataset.")
    if subject_id is not None and subject_id not in _SUBJECT_IDS:
        return _fail(f"Patient {subject_id} was not found in the dataset.")

    itemid, lab_label = _resolve_lab(cleaned, hadm_id)
    question_id = _classify(cleaned, has_lab=itemid is not None)

    if question_id is None:
        return _fail("Could not recognise the question. Try wording it like the examples, or use the dropdown above.")

    spec = questions.get_question(question_id)
    needs = set(inspect.signature(spec.func).parameters)
    params = {}

    if "hadm_id" in needs:
        if hadm_id is None:
            return _fail("Please include an admission ID, for example 'admission 145834'.")
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
        dates = re.findall(r"\d{4}-\d{2}-\d{2}", cleaned)
        if len(dates) < 2:
            return _fail("Please include a start and end date (YYYY-MM-DD).")
        params["start_time"], params["end_time"] = dates[0], dates[1]

    detail = []
    if "hadm_id" in params:
        detail.append(f"admission {params['hadm_id']}")
    if "subject_id" in params:
        detail.append(f"patient {params['subject_id']}")
    if lab_label and "itemid" in params:
        detail.append(f"lab {lab_label} (ITEMID {params['itemid']})")
    message = f"[{question_id}] {spec.label}" + (" | " + ", ".join(detail) if detail else "")

    return {
        "matched": True,
        "question_id": question_id,
        "params": params,
        "lab_label": lab_label,
        "message": message,
    }
