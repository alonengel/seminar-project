# Presentation Slides (outline)

Editable outline for the final presentation. A generated PowerPoint version is
at `docs/Clinical_Lab_Analysis_System.pptx` (built from this content by
`docs/build_pptx.py`).

---

## Slide 1 - Title
**Clinical Lab Analysis System**
MIMIC-III based system for predefined clinical laboratory questions
Team: Hala Hillou, Dana Nmarny, Anas Khoury, Alon Engel

## Slide 2 - Problem and goal
- Raw MIMIC-III lab data is large and hard to query ad hoc.
- Goal: automatically answer a defined set of clinical questions about an
  admission, a lab test, or a patient - reliably, transparently, reproducibly.
- Each answer ships with the exact code that produced it.

## Slide 3 - Data: source and preparation (Part 1)
- Source: MIMIC-III tables ADMISSIONS, LABEVENTS, and D_LABITEMS.
- Schema inspection: confirmed required fields exist (HADM_ID, ITEMID,
  CHARTTIME, VALUENUM, VALUEUOM, FLAG, LABEL) and checked missing values.
- Cleaning/filtering: drop lab rows without HADM_ID (needed for the join),
  keep valid VALUENUM for numeric analysis, join LABEVENTS to ADMISSIONS on
  HADM_ID, add readable lab names from D_LABITEMS (ITEMID -> LABEL).
- Result: one cleaned, merged dataset used by every question.

## Slide 4 - What the system does
- Takes one predefined question + parameters.
- Generates executable Python code, runs it, validates, corrects if needed,
  presents the result and the generated code.
- 12 supported question types (the 5 base questions from Part 1, plus 7).

## Slide 5 - Architecture
- Layered, registry-driven pipeline:
  question id -> generate code -> execute -> validate -> correct -> present.
- One question registry is the single source of truth: UI, generation,
  validation, and pipeline all read from it - adding a question is a one-place change.

## Slide 6 - The 12 questions
- Base (Part 1): abnormal results, latest value, trend over time, all tests,
  first-vs-last comparison.
- Added: summary stats (min/max/mean), abnormal vs normal counts,
  abnormal-by-test, distinct abnormal tests, values in a date range,
  patient admissions.
- Dataset-wide aggregate: abnormal vs normal counts across all admissions.

## Slide 7 - Code generation, validation, correction
- Template generation: `result = get_lab_trend(107521, 51221)`.
- Validation: expected columns + per-question rules (e.g. only-abnormal,
  single-row, time-ascending, counts add up).
- Correction: bounded rule-based retry that repairs generated-code errors.

## Slide 8 - Controlled natural language (optional LLM routing)
- Optional free-text box routes a question to ONE supported template.
- The model only selects a template id + parameters - it never writes code,
  and it may decline when nothing fits (no forced approximate match).
- Rule-based by default; optional LLM fallback (Anthropic/OpenAI/Gemini) when
  an API key is set. Keys live only in a gitignored `.env`.

## Slide 9 - Advanced: guarded LLM code-generation (AgentCoder-style)
- Optional "Advanced" mode: an LLM programmer agent writes pandas code for
  free-form questions, in a generate -> run -> validate -> refine loop.
- Guardrails: AST allowlist (no imports, dunders, file/network, loops) +
  restricted exec exposing only `pd` and a read-only `df`, with a timeout and
  row cap; a deterministic validator gates every result.
- Inspired by AgentCoder (arXiv 2312.13010); lightweight, in-repo orchestration
  (no CrewAI/AutoGen). Off by default and clearly labelled experimental.

## Slide 10 - User interface
- Three modes: Rules only | Rules, then AI | Advanced: AI writes code.
- Question selection + dynamic inputs + help captions.
- Escalation dialog: if a template cannot match, one click re-runs in Advanced.
- Results: metric cards, trend chart, color-coded status, generated-code tab.

## Slide 11 - Evaluation
- All 12 question types pass execution + validation across multiple admissions.
- Examples: Chloride latest 103 mEq/L; Hematocrit trend 57.9% -> 44.4%;
  pO2 first 82 / last 103 (+21 mm Hg).
- NL queries reproduce the same results as the structured dropdown.

## Slide 12 - Quality and engineering
- Modular design, single source of truth, docstrings.
- 159 automated tests, ~93% line coverage (85% gate); all run offline.
- Managed with uv; secrets only in `.env`; clean, logical git history.

## Slide 13 - Demo
- Structured trend question -> chart and generated code.
- Same question in natural language -> identical result.
- Force a correction (demo typo toggle) -> the corrector repairs the code.
- Edge case: unknown admission -> clear "not found".

## Slide 14 - Limitations and future work
- Predefined questions remain the trusted, default core; free-form code-gen is
  optional and guarded.
- Future: broaden the guarded code-gen catalog, a live SQL backend, richer
  charts, and presentation polish.
