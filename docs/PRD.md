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

**Out of scope:** free-text/unbounded questions, multi-table ad-hoc SQL,
external/LLM API calls, writes back to the dataset, authentication, and
multi-user state.

## 5. Functional requirements

1. Select a question (grouped by category) and its required parameters only.
2. Generate readable Python code from the selected question + parameters.
3. Execute the generated code safely against the prepared dataset.
4. Validate the result (expected columns, shape, and per-question rules).
5. Apply rule-based correction and retry on failure (bounded attempts).
6. Present the result, generated code, validation details, and correction
   attempts; allow CSV download.

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

## 8. Assumptions, dependencies, constraints

- `cleaned_merged_dataset.csv` is present locally (kept out of git for size;
  retrieval documented in `docs/decisions/decision-log.md`).
- Only lab rows with a valid `HADM_ID` are used.
- Depends on `pandas` and `streamlit` (see `requirements.txt`).

## 9. Team

Data preparation and question design: Hala, Dana. Architecture, code
generation, execution, validation, correction, and presentation: Anas, Alon.
