# Clinical Lab Analysis System

A MIMIC-III based system that answers a fixed set of predefined clinical
laboratory questions. For each question it **generates executable Python code**,
**runs** it on a cleaned MIMIC-III dataset, **validates** the output,
**auto-corrects** simple errors, and **presents** the result in a Streamlit UI.

It is intentionally scoped to predefined questions only (no free-text / unlimited
medical questions), in line with the project guide.

## How it works

```
question id -> code generation -> execution -> validation -> correction (if needed) -> presentation
```

All supported questions live in a single **question registry**
(`questions.py`). Every module reads from it, so adding a question is a
one-place change (see "Adding a new question" below).

### Modules

| File | Responsibility |
| --- | --- |
| `data_prep.py` | Loads the dataset and defines one data-prep function per question |
| `questions.py` | The `QuestionSpec` registry + parameter definitions (single source of truth) |
| `code_generation.py` | Builds the runnable code string from a `QuestionSpec` |
| `execution.py` | Safely `exec()`s the generated code and captures the result/error |
| `validation.py` | Checks columns / shape / per-question rules from the spec |
| `correction.py` | Rule-based fixes + retry loop |
| `result_presentation.py` | Console presentation (used by the pipeline path) |
| `main_pipeline.py` | Wires the modules into `run_pipeline(question_id, params)` |
| `app.py` | Streamlit UI |
| `question_router.py` / `llm_router.py` / `llm_client.py` | Optional natural-language routing (rule-based, with an optional LLM fallback) |
| `sandbox.py` / `code_agent.py` / `agent_pipeline.py` / `presentation_agent.py` | Experimental LLM code-generation agent (see below) |

## Supported questions

1. Show abnormal lab results for a specific admission
2. Return the latest value of a selected lab test during an admission
3. Show the trend of a selected lab test over time during an admission
4. Show all lab tests performed during a specific admission
5. Compare the first and last numeric value of a selected lab test
6. Show summary statistics (min/max/mean) of a lab test during an admission
7. Count abnormal vs normal results during an admission
8. Show abnormal results for a specific lab test during an admission
9. List all abnormal flagged lab tests during an admission
10. Show lab values within a date range during an admission
11. List all admissions for a specific patient
12. Count abnormal vs normal results across all admissions (dataset-wide aggregate)

## Setup

1. Python 3.10+.
2. Install [uv](https://docs.astral.sh/uv/), then install dependencies:

```bash
uv sync
```

3. Place `cleaned_merged_dataset.csv` in the project root (next to `app.py`).
   The dataset is not stored in git because of its size - see
   `docs/decisions/decision-log.md` for how to obtain it.

## Run

Streamlit UI:

```bash
uv run streamlit run app.py
```

Console (single pipeline run):

```bash
uv run python main_pipeline.py
```

## Natural-language input (optional)

Besides the dropdown, you can type a question in plain English; it is routed
to one of the supported questions, for example:

- "Show abnormal lab results for admission 145834"
- "What is the latest chloride value for admission 199884?"
- "Show hematocrit trend for admission 107521"
- "Show abnormal lab results for all admissions" (dataset-wide aggregate)

The router only selects a predefined question and extracts its parameters - it
never generates or runs free-form code. Routing is **rule-based by default**; set
an LLM API key in `.env` (copy `.env.example`) to enable an optional
**LLM-assisted** fallback (`llm_router.py`) that still maps only to the supported
questions. The provider (Anthropic / OpenAI / Gemini) is chosen by which key is set.

## Advanced: AI writes code (experimental)

With an LLM key set, the natural-language box offers an extra **"Advanced: AI
writes code"** mode. Inspired by [AgentCoder](https://arxiv.org/abs/2312.13010),
a programmer agent (LLM) writes a pandas snippet for a free-form question, which
runs in a generate -> execute -> validate -> refine loop:

```
question -> code_agent (LLM) -> sandbox.check_code (AST allowlist) -> sandbox exec -> validate_freeform -> retry on failure
```

It stays controlled: the snippet runs in `sandbox.py` with a restricted builtins
namespace exposing only `pd` and a read-only `df` - no imports, file/network
access, dunder/underscore attributes, or loops - in a worker thread with a soft
timeout and a row cap, and the result must pass a deterministic validator before
it is shown. The orchestration is lightweight and in-repo (no CrewAI/AutoGen).
This mode is **off by default and experimental**; the 12-question registry
remains the trusted default.

When a template mode (Rules only / Rules, then AI) cannot match a question -
e.g. *"last 10 abnormal results across the whole database"* - and an LLM key is
set, a popup offers to re-run it in Advanced mode (or cancel); accepting it
switches the mode selector to Advanced and runs the query automatically, so you
are never left at a dead end.

## Adding a new question

1. Add a data-prep function in `data_prep.py` that returns a `DataFrame`.
2. Add a `QuestionSpec(...)` entry to `QUESTION_REGISTRY` in `questions.py`
   (id, label, params, func, expected_columns, optional validator/chart).
   Dataset-wide questions take no input - use `params=[]` and a zero-argument
   function (see Q12).
3. If it needs a new input type, add an entry to `PARAM_DEFS`.

No changes to `app.py`, `code_generation.py`, `validation.py`, or
`main_pipeline.py` are required - they all read from the registry.

## Tests

Unit tests plus an end-to-end test (via Streamlit's `AppTest`) that exercises
all 12 questions live in `tests/`:

```bash
uv run pytest
```

105 tests, 93% line coverage. See `docs/TEST_REPORT.md` for per-question expected
results and `docs/assets/screenshots/` for a UI screenshot of each question.

## Project documentation

- `docs/PRD.md` - product requirements
- `docs/PLAN.md` - architecture and design
- `docs/TODO.md` - task tracking
- `docs/REPORT.md` - final project report
- `docs/DEMO.md` - demo walkthrough script
- `docs/SLIDES.md` - presentation outline (+ generated `Clinical_Lab_Analysis_System.pptx`)
- `docs/plans/` - implementation plans
- `docs/decisions/decision-log.md` - decisions and progress log
- `docs/TEST_REPORT.md` - test results, coverage, and per-question expectations
- `docs/guidelines-gap-analysis.md` - mapping to professional-software guidelines
- `docs/assets/screenshots/` - per-question UI screenshots
