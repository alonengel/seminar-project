# Product Requirements Document (PRD)

## 1. Overview and context

The Clinical Lab Analysis System is a decision-support MVP built on the
MIMIC-III hospital dataset. A user picks one of a fixed set of predefined
clinical laboratory questions; the system generates executable Python code for
it, runs that code on a cleaned dataset, validates the output, applies a simple
correction if needed, and presents the result.

It demonstrates a controlled "generated code + self-correction" workflow without
allowing free-text or unbounded medical questions.

## 2. Problem and users

- **Problem:** raw MIMIC-III lab data is large and hard to query ad hoc;
  clinicians/researchers need quick, reliable answers to a small set of
  well-defined questions about an admission or a lab test.
- **Target users:** clinical/research users exploring lab data for an admission
  or patient, and course evaluators reviewing the system.

## 3. Goals and success criteria

- Answer every supported question correctly from the cleaned dataset.
- Show the full pipeline transparently: generated code, validation status, and
  whether a correction was applied.
- Be reliable: clear handling of empty results and errors.
- **Acceptance criteria:**
  - All supported questions pass execution and validation across multiple
    admissions/patients.
  - Automated tests pass with >= 85% coverage.
  - The UI renders the correct inputs and results for each question.

## 4. Scope

**In scope:** a fixed registry of predefined questions; the cleaned MIMIC-III
merge of ADMISSIONS + LABEVENTS (+ lab labels); a Streamlit UI; CSV export.
Optional, off-by-default LLM features: natural-language routing to a template and
an experimental guarded code-generation mode (sandboxed; see the decision log).

**Out of scope (by default):** free-text/unbounded questions as the primary path,
multi-table ad-hoc SQL, unsandboxed code execution, writes back to the dataset,
authentication, and multi-user state.

## 5. Functional requirements

1. Select a question (grouped by category) and its required parameters only.
2. Generate readable Python code from the selected question + parameters.
3. Execute the generated code safely against the prepared dataset.
4. Validate the result (expected columns, shape, and per-question rules).
5. Apply rule-based correction and retry on failure (bounded attempts).
6. Present the result, generated code, validation details, and correction
   attempts; allow CSV download.
7. Optionally accept a natural-language question and route it (rule-based) to one
   of the supported questions, extracting its parameters.

## 6. Non-functional requirements

- **Usability:** controlled inputs, readable dark theme, clear success / empty /
  failure states.
- **Reliability:** graceful "no matching records" handling; no crash on bad input.
- **Maintainability:** questions defined once in a registry; adding one is a
  single-place change.
- **Performance:** filtering ~1M rows returns within a couple of seconds.
- **Portability:** runs locally with Python + pandas + Streamlit.

## 7. Supported questions

| # | Question | Inputs |
| --- | --- | --- |
| 1 | Abnormal lab results for an admission | Admission |
| 2 | Latest value of a lab test | Admission, Lab Test |
| 3 | Trend of a lab test over time | Admission, Lab Test |
| 4 | All lab tests during an admission | Admission |
| 5 | Compare first vs last value of a lab test | Admission, Lab Test |
| 6 | Summary statistics (min/max/mean) of a lab test | Admission, Lab Test |
| 7 | Count abnormal vs normal results | Admission |
| 8 | Abnormal results for a specific lab test | Admission, Lab Test |
| 9 | List distinct abnormal lab tests | Admission |
| 10 | Lab values within a date range | Admission, Lab Test, Date range |
| 11 | All admissions for a patient | Patient |
| 12 | Abnormal vs normal counts across all admissions | None (dataset-wide) |

## 8. Assumptions, dependencies, constraints

- `cleaned_merged_dataset.csv` is present locally (kept out of git for size;
  retrieval documented in `docs/decisions/decision-log.md`).
- Only lab rows with a valid `HADM_ID` are used.
- Depends on `pandas` and `streamlit`; managed with `uv` (see `pyproject.toml`).

## 9. Team

Data preparation and question design: Hala, Dana. Architecture, code
generation, execution, validation, correction, and presentation: Anas, Alon.

## 10. Controlled AI / NLP and LLM usage

The system includes a controlled AI/NLP question-routing layer
(`question_router.py`) that maps a natural-language clinical lab question into one
of the supported question templates and extracts its parameters (admission ID, lab
test, patient ID, dates). The router only selects a predefined question; it never
generates or executes free-form code, and it rejects anything it cannot map.

Two routing modes share the same validation (`question_router.build_route_result`):

- **Rule-based** (`question_router.route_question`): keyword/pattern matching - the
  default, always available, fast, and deterministic.
- **LLM-assisted** (`llm_router.py`, optional): used as a fallback when the rules
  cannot match and an LLM provider key is configured. The model returns ONLY a JSON
  object choosing a question id + parameters, which is parsed and validated against
  the registry. The LLM never generates code.

LLM support is OFF by default - with no API key the system uses only the rule-based
router. The provider (Anthropic / OpenAI / Gemini) is selected by which key is set
(see `.env.example`). This keeps behaviour reliable, testable, and reproducible
while allowing richer natural-language understanding when a key is provided.
