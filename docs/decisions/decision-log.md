# Decision & Progress Log

A running log of decisions and progress for the Clinical Lab Analysis System (seminar project).
Newest entries at the top.

## 2026-06-13

### Step 17 implementation (completed)
- Refactored the 5 hardcoded questions into a config-driven registry (`questions.py`) backed by data functions in `data_prep.py`. Every module (code generation, validation, correction, pipeline, UI) now reads from the registry, so adding a question is a one-place change.
- Added 6 new question types (11 total): summary statistics (Q6), abnormal vs normal counts (Q7), abnormal results for a specific test (Q8), distinct abnormal tests with counts (Q9), values within a date range (Q10), and all admissions for a patient (Q11).
- Q9 refinement: implemented as a deduplicated list of distinct abnormal tests with per-test counts, rather than a row-by-row abnormal dump, to avoid redundancy with Q1 ("show abnormal lab results").
- UI (`app.py`): registry-driven question dropdown with a category filter, parameter widgets rendered dynamically from each question's declared params (including the new patient-id and date-range inputs), a fixed result banner (no longer always green; now reflects success / no-records / failure), and a trend line chart for time-series questions.
- Bug fix: the rule-based typo corrector used naive substring replacement, which corrupted the valid name `get_abnormal_results_for_lab`. It now matches whole identifiers only (word boundaries).
- Cleanup / deliverables: removed leftover mock code from `code_generation.py`, added `requirements.txt` and `README.md`, and updated the two test scripts to the new spec-based signatures.
- Verification: smoke-tested all 11 questions end-to-end (execution + validation pass) and both test scripts pass. The Streamlit UI was not launched here (streamlit is not installed in this environment); run `pip install -r requirements.txt` then `streamlit run app.py` to view it.

### Repository setup
- Initialized git in the project folder on branch `main`.
- Connected remote `origin` = `git@github.com:alonengel/seminar-project.git` (remote was empty; SSH reachable).
- Added `.gitignore`.

### Dataset handling (DECIDED)
- Decision: keep the dataset OUT of git and document how to obtain it. (Git LFS not used, to avoid quota/setup overhead.)
- `cleaned_merged_dataset.csv` (~130 MB) exceeds GitHub's 100 MB per-file hard limit; `cleaned_merged_dataset.csv.xlsx` (~53 MB) is a redundant Excel copy. Both are git-ignored.

#### How to obtain the dataset
- `cleaned_merged_dataset.csv` is a cleaned merge of the MIMIC-III tables ADMISSIONS + LABEVENTS (plus D_LABITEMS for readable lab `LABEL`s), filtered to lab rows with a valid `HADM_ID` (per Steps 3-4 of the team guide).
- Columns: `SUBJECT_ID_x, HADM_ID, ITEMID, CHARTTIME, VALUENUM, VALUEUOM, FLAG, SUBJECT_ID_y, ADMITTIME, DISCHTIME, DIAGNOSIS, LABEL`.
- Place the file in the project root (next to `app.py`) before running the app.
- Source: the team's shared storage (add link here), or regenerate from MIMIC-III following Steps 3-4. The forthcoming README will include the exact steps/link.

### Step 17 scope (agreed)
- Implement Step 17 of the guide: support more than 5 questions, improve the UI, and clean up.
- Approach: refactor the 5 currently-hardcoded questions into a single config-driven "question registry" so adding a question is a one-place change.
- "Dynamic" decision: YES to a developer-facing registry (single source of truth); NO to runtime user-defined/free-text questions (explicitly out of scope per the guide; would break validation and safe execution).
- Keep question IDs 1-5 stable so the existing Step 16 evaluation stays valid.
- Full plan: see `docs/plans/step-17-registry-refactor.md`.

### Status
- Plan written and mirrored into the repo.
- Baseline + plan/docs committed and pushed to `origin`.
- Step 17 fully implemented and verified (pipeline + all 11 questions). Streamlit UI pending a manual run with streamlit installed.
- Implementation commit pending (awaiting go-ahead to commit/push).
