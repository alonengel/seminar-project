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

## Setup

1. Python 3.10+.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Place `cleaned_merged_dataset.csv` in the project root (next to `app.py`).
   The dataset is not stored in git because of its size - see
   `docs/decisions/decision-log.md` for how to obtain it.

## Run

Streamlit UI:

```bash
streamlit run app.py
```

Console (single pipeline run):

```bash
python main_pipeline.py
```

## Adding a new question

1. Add a data-prep function in `data_prep.py` that returns a `DataFrame`.
2. Add a `QuestionSpec(...)` entry to `QUESTION_REGISTRY` in `questions.py`
   (id, label, params, func, expected_columns, optional validator/chart).
3. If it needs a new input type, add an entry to `PARAM_DEFS`.

No changes to `app.py`, `code_generation.py`, `validation.py`, or
`main_pipeline.py` are required - they all read from the registry.

## Tests

```bash
python test_correction.py
python test_result_presentation.py
```

## Project documentation

- `docs/plans/` - implementation plans
- `docs/decisions/decision-log.md` - decisions and progress log
