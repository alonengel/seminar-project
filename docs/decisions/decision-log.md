# Decision & Progress Log

A running log of decisions and progress for the Clinical Lab Analysis System (seminar project).
Newest entries at the top.

## 2026-06-13

### UI improvements
- Added a one-line help caption under each selected question (what it returns + the inputs it needs).
- Richer result presentation: summary metric cards (latest value / first-vs-last / min-max-mean / abnormal counts / row count), an Altair trend chart with axis labels and lab units (questions 3 and 10), and color-coded status indicators (green pass / red fail / blue no-records).
- A sidebar and a header badge row were tried but removed as unnecessary per review.
- All 72 tests still pass (~94% coverage); regenerated the per-question screenshots.

### Controlled natural-language routing (no LLM in MVP)
- Added `question_router.py`: a rule-based/keyword router that maps a free-text clinical lab question to exactly one of the 11 supported question templates and extracts its parameters (admission, lab test, patient, dates). It only selects predefined questions and never generates free-form code.
- Added an optional "Ask in natural language" box to the Streamlit UI; a matched query drives the same pipeline as the dropdown (e.g. "Show hematocrit trend for admission 107521").
- Decision: no LLM in the MVP - predefined questions plus template-based generation are more reliable, testable, and reproducible. An LLM-assisted router / NL interface is future work and can replace the rule-based router without changing the pipeline.
- Tests: added router unit tests + NL end-to-end tests (70 tests total, ~94% coverage).
- Confirmed against the row-2 project brief: all five required components and inputs are covered; the NL layer strengthens alignment with the stated goal of automatically answering clinical questions.

### Switched to uv for dependency management
- Adopted `uv` with a `pyproject.toml` (dependencies + a `dev` group + pytest/coverage config) and a committed `uv.lock`; removed `requirements.txt`.
- App and tests now run via `uv run` (`uv run streamlit run app.py`, `uv run pytest`); the coverage gate is set to 85% in `pyproject.toml`.
- `uv sync` builds a local `.venv` (uv selected CPython 3.13); the suite passes there (56 tests, ~94% coverage).

### Testing, coverage, and UI verification
- Added a `tests/` suite: unit tests for every logic module plus an end-to-end test (Streamlit `AppTest`) covering all 11 questions, Q8 happy + no-records edge cases, and the category filter. 56 tests pass at 94% line coverage (target 85%).
- Verified the running app in a real headless Chromium browser and captured a screenshot of each question (`docs/assets/screenshots/q01..q11.png`).
- Fixed two UI rendering issues found during verification: empty context "cards" (now `st.container(border=True)`) and a light/dark theme mismatch that made headers unreadable (now pinned via `.streamlit/config.toml`).
- Replaced the two ad-hoc root test scripts with the `tests/` suite; added `docs/TEST_REPORT.md` and `docs/guidelines-gap-analysis.md` (a mapping against common professional software-engineering practices, treated as inspiration; heavier mandates like uv/SDK/150-line splits are noted as optional).
- Tooling: installed `pytest`, `pytest-cov`, and `playwright` as dev dependencies (later moved under uv; see the entry above).

### Step 17 implementation (completed)
- Refactored the 5 hardcoded questions into a config-driven registry (`questions.py`) backed by data functions in `data_prep.py`. Every module (code generation, validation, correction, pipeline, UI) now reads from the registry, so adding a question is a one-place change.
- Added 6 new question types (11 total): summary statistics (Q6), abnormal vs normal counts (Q7), abnormal results for a specific test (Q8), distinct abnormal tests with counts (Q9), values within a date range (Q10), and all admissions for a patient (Q11).
- Q9 refinement: implemented as a deduplicated list of distinct abnormal tests with per-test counts, rather than a row-by-row abnormal dump, to avoid redundancy with Q1 ("show abnormal lab results").
- UI (`app.py`): registry-driven question dropdown with a category filter, parameter widgets rendered dynamically from each question's declared params (including the new patient-id and date-range inputs), a fixed result banner (no longer always green; now reflects success / no-records / failure), and a trend line chart for time-series questions.
- Bug fix: the rule-based typo corrector used naive substring replacement, which corrupted the valid name `get_abnormal_results_for_lab`. It now matches whole identifiers only (word boundaries).
- Cleanup / deliverables: removed leftover mock code from `code_generation.py`, added `requirements.txt` and `README.md`, and updated the two test scripts to the new spec-based signatures.
- Verification: smoke-tested all 11 questions end-to-end (execution + validation pass) and both test scripts pass. The Streamlit UI was not launched here (streamlit is not installed in this environment); run `uv sync` then `uv run streamlit run app.py` to view it.

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
- Step 17 fully implemented and verified (pipeline + all 11 questions).
- Implementation committed in 4 logical commits (refactor / new questions / UI / docs) and pushed to `origin`.
- Remaining: run the Streamlit UI manually (`uv sync`, then `uv run streamlit run app.py`), and replace the dataset "add link here" placeholder with the team's shared link.
