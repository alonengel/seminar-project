# Demo Walkthrough

A scripted demo of the Clinical Lab Analysis System for the presentation.
Each step lists what to do and the expected result. Screenshots of every
question are in `docs/assets/screenshots/`.

## 0. Setup

```bash
uv sync
uv run streamlit run app.py
```

Open http://localhost:8501. (Ensure `cleaned_merged_dataset.csv` is in the
project root.)

## 1. Orientation (30s)

Point out the flow described in the header: the system takes one predefined
question, **generates Python code, runs it, validates, corrects if needed, and
presents the result** - and supports 11 question types from a single registry.

## 2. Structured question - trend with a chart (Q3)

1. Category: **All**; Question: **"Show the trend of a selected lab test over time during an admission"**.
2. Admission ID: **107521**; Lab Test: **Hematocrit (ITEMID 51221)**.
3. Click **Run Analysis**.

**Expected:** green "Analysis completed successfully"; status row shows
Execution = success, Validation = Passed, Correction = No. The **Final Result**
tab shows a line chart with a clear downward trend (≈57.9% -> 44.4%) and the
table. The **Generated Code** tab shows `result = get_lab_trend(107521, 51221)`.

## 3. Same question in natural language (controlled AI)

1. Expand **"Ask a clinical lab question in natural language (optional)"**.
2. Type: **`Show hematocrit trend for admission 107521`** and click **Interpret & Run**.

**Expected:** a blue "Interpreted as: [3] ... admission 107521, lab Hematocrit
(ITEMID 51221)" message, then the identical result as step 2. Emphasize: the
router maps the sentence to a predefined template + parameters - it does **not**
generate free-form code, and no LLM is used.

## 4. A few more questions (pick 2-3)

- **Q2 latest value:** `What is the latest chloride value for admission 199884?`
  -> latest Chloride ≈ 103 mEq/L (one row; metric card "Latest value").
- **Q5 first vs last:** admission **177047**, lab **pO2 (50821)** -> First 82,
  Last 103, **Difference +21 mm Hg** (metric cards).
- **Q6 summary stats:** any admission + lab -> Count / Min / Max / Mean cards.
- **Q11 patient:** Question "List all admissions for a specific patient",
  Patient ID e.g. **3** -> the patient's admissions (note: only a Patient input
  is shown - the UI renders inputs per question).

## 5. Validation and correction tabs

After any run, open the **Validation Details** tab (shows the validation rule
that passed) and the **Correction Attempts** tab (shows "No correction attempts
were needed" for normal runs). Mention that correction is a bounded rule-based
retry loop for generated-code errors.

## 6. Edge case - graceful handling

In the natural-language box, type **`Show hematocrit trend for admission 107522`**
(a non-existent admission). 

**Expected:** a clear message **"Admission 107522 was not found in the dataset."**
- the router validates inputs and rejects unmappable questions instead of
guessing.

## 7. Wrap-up talking points

- Single question registry -> adding a question is a one-place change.
- Template-based generation + validation + correction = reliable, testable,
  reproducible (no LLM in the MVP; LLM interface is future work).
- 72 automated tests, ~94% coverage; per-question screenshots in `docs/`.
