# Test Report

Automated tests for the Clinical Lab Analysis System.

## Summary

- **170 tests pass**, **0 failures**.
- **94% line coverage** (target: 85%).
- Layers covered: unit tests for every logic module (including the code-gen
  sandbox, programmer agent, and orchestration loop) + an end-to-end test for the
  Streamlit UI that enters both role workspaces (Doctor / Researcher) and
  exercises **all 12 questions** and the experimental code-gen mode.

Run them with:

```bash
uv sync
uv run pytest
```

(Coverage is configured in `pyproject.toml` with an 85% minimum gate.)

## Coverage

| Module | Coverage |
| --- | --- |
| `agent_pipeline.py` | 100% |
| `code_generation.py` | 100% |
| `correction.py` | 100% |
| `execution.py` | 100% |
| `llm_router.py` | 100% |
| `result_presentation.py` | 100% |
| `sandbox.py` | 99% |
| `data_prep.py` | 96% |
| `main_pipeline.py` | 95% |
| `validation.py` | 95% |
| `app.py` | 94% |
| `code_agent.py` | 94% |
| `presentation_agent.py` | 92% |
| `question_router.py` | 91% |
| `questions.py` | 91% |
| `llm_client.py` | 90% |
| **Total** | **94%** |

## End-to-end results per question

Each question is selected in the app, the correct parameter widgets are
asserted to render, the analysis is run, and the result components are checked.
These were verified both via Streamlit's `AppTest` harness (`tests/test_e2e_app.py`)
and in a real headless Chromium browser (screenshots in `docs/assets/screenshots/`).

| # | Question | Widgets shown | Expected result | Status |
| --- | --- | --- | --- | --- |
| 1 | Abnormal lab results | Admission | Table, all `FLAG = abnormal` | Pass |
| 2 | Latest lab value | Admission, Lab Test | Exactly 1 row | Pass |
| 3 | Lab trend over time | Admission, Lab Test | Time-sorted table + line chart | Pass |
| 4 | All lab tests | Admission | Table of all tests | Pass |
| 5 | First vs last value | Admission, Lab Test | 1-row comparison incl. difference | Pass |
| 6 | Summary statistics | Admission, Lab Test | 1 row: count/min/max/mean | Pass |
| 7 | Abnormal vs normal counts | Admission | 1 row: total/abnormal/normal | Pass |
| 8 | Abnormal results for a lab | Admission, Lab Test | Abnormal rows, or graceful "no records" | Pass |
| 9 | Distinct abnormal tests | Admission | Table of tests with abnormal counts | Pass |
| 10 | Values in a date range | Admission, Lab Test, Date range | Time-sorted table + line chart | Pass |
| 11 | All admissions for a patient | Patient ID | Table of the patient's admissions | Pass |
| 12 | Abnormal vs normal across all admissions | (none - dataset-wide) | One row per admission: total/abnormal/normal, most abnormal first | Pass |

## Edge cases covered

- **No-records path**: question 8 with a lab that has no abnormal readings shows
  the neutral "no matching records" banner instead of an error.
- **Correction loop**: a generated function-name typo is auto-corrected and re-run.
- **Regression guard**: the typo corrector no longer corrupts the valid name
  `get_abnormal_results_for_lab` (it matches whole identifiers only).
- **Missing data**: data functions return empty frames for unknown admissions/patients.
- **Validation failures**: execution error, `None` result, non-DataFrame, missing
  columns, empty frame, and failing per-question rules are all handled.
- **Dataset-wide aggregate (Q12)**: per-admission counts are cross-checked against the
  single-admission view (Q7), and `Abnormal + Normal == Total Tests` is validated for
  every row. The "all admissions" natural-language query routes here (rules and LLM)
  instead of demanding an admission ID.
- **Code-gen sandbox (experimental mode)**: imports, `open`, dunder/underscore
  attributes, file/network/eval methods (`to_csv`, `query`, ...), loops, and syntax
  errors are all rejected by the AST allowlist; runtime errors, timeouts, and row
  caps are handled. The agent loop is tested end-to-end with a fake LLM: it refines
  after a runtime error, blocks malicious code, and degrades gracefully on LLM errors.

## Example (question 11, patient overview)

![Question 11 - patient admissions](assets/screenshots/q11.png)
