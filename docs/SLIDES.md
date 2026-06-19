# Presentation Slides (outline)

Editable outline for the final presentation. A generated PowerPoint version is
at `docs/Clinical_Lab_Analysis_System.pptx` (built from this content).

---

## Slide 1 - Title
**Clinical Lab Analysis System**
MIMIC-III based system for predefined clinical laboratory questions
Team: Hala Hillou, Dana Nmarny, Anas Khoury, Alon Engel

## Slide 2 - Problem
- Raw MIMIC-III lab data is large and hard to query ad hoc.
- Goal: automatically answer a limited set of clinical questions about an
  admission, a lab test, or a patient - reliably and transparently.

## Slide 3 - What the system does
- Takes one predefined question + parameters.
- Generates executable Python code, runs it, validates, corrects if needed,
  presents the result and the generated code.
- 12 supported question types.

## Slide 4 - Architecture
- Layered, registry-driven pipeline:
  question id -> generate code -> execute -> validate -> correct -> present.
- One question registry is the single source of truth (UI, generation,
  validation, pipeline all read from it).

## Slide 5 - The 12 questions
- Abnormal results, latest value, trend, all tests, first-vs-last, summary stats,
  abnormal vs normal counts, abnormal-by-test, distinct abnormal tests,
  date-range values, patient admissions.
- Plus a dataset-wide aggregate: abnormal vs normal counts across all admissions.

## Slide 6 - Code generation, validation, correction
- Template generation: `result = get_lab_trend(107521, 51221)`.
- Validation: expected columns + per-question rules.
- Correction: bounded rule-based retry for generated-code errors.

## Slide 7 - Controlled AI / NLP (optional LLM)
- Optional natural-language box routes free text to ONE supported template.
- Never generates free-form code; rejects unmappable input.
- Rule-based by default; optional LLM-assisted fallback (Anthropic/OpenAI/Gemini)
  when an API key is set - the model only selects a template.

## Slide 8 - User interface
- Question selection + dynamic inputs + help captions.
- Results: metric cards, trend chart, color-coded status, generated-code tab.

## Slide 9 - Evaluation
- All question types pass execution + validation across multiple admissions.
- Examples: Chloride latest 103 mEq/L; Hematocrit trend 57.9% -> 44.4%;
  pO2 first 82 / last 103 (+21 mm Hg).

## Slide 10 - Quality / engineering
- Modular design, single source of truth, docstrings.
- 105 automated tests, ~93% coverage (85% gate); managed with uv; clean git history.

## Slide 11 - Demo
- Structured trend question -> chart.
- Same question in natural language -> identical result.
- Edge case: unknown admission -> clear "not found".

## Slide 12 - Limitations and future work
- Predefined questions only (by design).
- Future: LLM-assisted routing, broader question set, live SQL backend.
