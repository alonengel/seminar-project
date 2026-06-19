# Decision & Progress Log

A running log of decisions and progress for the Clinical Lab Analysis System (seminar project).
Newest entries at the top.

## 2026-06-19

### Optional guarded LLM code-generation agent (AgentCoder-style)
- Added an experimental "Advanced: AI writes code" mode: a programmer agent (LLM) writes pandas code to answer free-form questions, executed in a sandbox and gated by a deterministic validator, in a generate-run-validate-refine loop. Inspired by AgentCoder (arXiv 2312.13010), which uses a programmer agent, an independent validator/test role, and a plain-Python executor.
- This deliberately reverses the earlier "no LLM code generation" scope decision, but keeps it controlled: the LLM only proposes code; the sandbox + validator dispose. The 12-question registry stays the default, trusted core; code-gen is off by default and clearly labelled experimental.
- New modules: `sandbox.py` (AST allowlist - no imports, dunder/underscore attributes, file/network/eval methods, or loops - plus a restricted-`__builtins__` exec that exposes only `pd` and a read-only `df`, run in a worker thread with a soft timeout and a row cap); `code_agent.py` (the programmer agent; schema-aware prompt, refine-on-feedback, injectable `complete_fn`); `agent_pipeline.py` (`run_codegen` loop mirroring `run_with_correction`'s result shape); `presentation_agent.py` (rule-based chart suggestion with an optional LLM override). `validation.validate_freeform_result` is the generic gate; `llm_client.complete` gained a `max_tokens` argument.
- Orchestration: kept lightweight and in-repo (no CrewAI/AutoGen/LangGraph). AgentCoder's own analysis shows that adding more agents/frameworks mainly adds token and coordination overhead; three roles - two of which we already had as deterministic modules - are enough.
- Escalation UX: when a template mode cannot match a question and an LLM provider is configured, a modal (`st.dialog`) offers to re-run it in Advanced code-gen mode, or cancel; accepting it moves the mode selector to Advanced and runs the query automatically, so an unanswerable template query is one click from being answered rather than a dead end. The offer (`escalation_text`) and the resulting code-gen output are persisted in `st.session_state` - the dialog is re-rendered each run so its buttons reliably register a click (a button created only on the submit run would otherwise lose the click on rerun).
- LLM "decline": the LLM router may now return `question_id: 0` when no template precisely answers (e.g. "last 10 abnormal results across the whole database" - specific rows / top-N), instead of forcing an approximate match (which previously mis-routed that query to the per-admission-counts template). A decline is treated as a no-match, which triggers the escalation dialog.
- Simplified the interpretation modes from four to three: dropped "AI only" from the UI (it forced an LLM call while skipping the free rule matcher, which "Rules, then AI" already covers as a fallback). The underlying `route(text, mode="llm")` path and its tests are kept in code in case the pure-LLM mode is wanted again.
- Added a clearly-labelled, off-by-default "Demo: inject a typo" checkbox (shown only for the original 5 questions, whose functions have a known typo). Because the template generator always emits correct code, the rule-based correction loop never fires in normal UI use; this toggle deliberately misspells the function name so the first attempt fails and the corrector visibly repairs it (two attempts, "Correction Applied: Yes"). The typo map was hoisted to `correction.TYPO_FIXES` (+ a `REVERSE_TYPOS` inverse) as the single source of truth, and `main_pipeline.run_pipeline` gained an `inject_typo` flag.
- Tests: +50 offline tests (sandbox escapes blocked, programmer agent, the loop with refine/blocked/error paths, the presentation agent, the router handoff, the escalation path, and end-to-end UI for the code-gen mode). Suite is now 155 tests at ~94% coverage. Secrets still only via `.env`; new `CODEGEN_*` tuning keys documented in `.env.example`.

### Dataset-wide aggregate question (Q12) + clearer per-admission routing
- Added a 12th question, "Count abnormal vs normal results across all admissions" - a param-less registry entry (`params=[]`, zero-argument data-prep function `get_abnormal_counts_all_admissions`) returning one row per admission (total/abnormal/normal), most abnormal first. It is the dataset-wide companion to Q7; a `_counts_consistent` validator checks `Abnormal + Normal == Total Tests` per row.
- The registry-driven UI/pipeline/code-gen/validation needed no structural change: a param-less question renders only the Run button, and the context panel shows a "runs across the entire dataset" note. Added aggregate metric cards (admissions / total abnormal / total tests).
- Routing: a natural-language "abnormal results for all admissions" now maps to Q12 (rule-based phrase detection; the LLM catalog already exposes it) instead of failing with "please include an admission ID". That per-admission failure message was reworded to explain the per-admission scope and point to the aggregate. Motivated by a user query ("...for all the admissions") that previously dead-ended in AI-only mode.
- Tests + docs: added data-prep (cross-checked against Q7), registry, and rule/LLM/end-to-end routing tests -> the suite is now 105 tests at ~93% coverage. Updated README/PRD/PLAN/REPORT/DEMO/SLIDES/TODO/TEST_REPORT to "12 questions".

### Optional LLM-assisted routing (supersedes the earlier "no LLM" decision)
- Added an optional LLM layer, adapted from the reference projects (ex4, alon_renat_ex03): `llm_client.py` (httpx-based; Anthropic/OpenAI/Gemini selected by which API key is set; mock/none fallback; retries on transient errors) and `llm_router.py` (asks the model for ONLY a JSON question id + parameters, parsed and validated against the registry - it never generates code).
- `question_router.smart_route` tries the rule-based router first and falls back to the LLM only when the rules fail and a provider key is configured. Shared validation was extracted into `build_route_result` so both routers enforce identical rules.
- Secrets via `.env` (gitignored) + `.env.example`; provider/model in env vars. Added `httpx` + `python-dotenv` dependencies (uv).
- The UI shows whether LLM routing is on/off and which method (rules/LLM) interpreted a query.
- Tests: +20 (llm_client, llm_router, smart_route/build_route_result) -> 92 tests, ~94% coverage. The earlier "no LLM in MVP" stance is now an optional, controlled enhancement (off by default; no code generation).

## 2026-06-13

### Step 18 - final deliverables
- Added `docs/REPORT.md` (full project report), `docs/DEMO.md` (demo walkthrough script), and `docs/SLIDES.md` plus a generated `docs/Clinical_Lab_Analysis_System.pptx` (12-slide deck built with python-pptx).
- Architecture diagrams remain as mermaid in `docs/PLAN.md` and `docs/REPORT.md`.
- Remaining team item: replace the dataset "add link here" placeholder with the team's shared download link.

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
