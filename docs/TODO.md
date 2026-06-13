# Task Tracking (TODO)

Status legend: [x] done, [~] in progress, [ ] not started.

## Phase 1 - MVP (Steps 1-16)

- [x] Freeze scope and choose 5 predefined question types
- [x] Inspect schema and build the cleaned merged dataset
- [x] Question selection, data preparation, code generation
- [x] Execution, validation, rule-based correction, result presentation
- [x] End-to-end integration and Streamlit UI
- [x] MVP evaluation across multiple admissions/patients

## Phase 2 - Step 17 (improve and polish)

- [x] Refactor to a config-driven question registry (single source of truth)
- [x] Add 6 new question types (now 11 total)
- [x] UI polish: category filter, dynamic parameter widgets, trend chart,
      fixed result banner
- [x] Cleanup: remove mock code; add `requirements.txt` and `README.md`
- [x] Fix bordered-card rendering and pin a dark theme
- [x] Test suite: unit + per-question end-to-end (56 tests, 94% coverage)
- [x] Per-question browser screenshots and `docs/TEST_REPORT.md`
- [x] Project docs: `PRD.md`, `PLAN.md`, `TODO.md`

## Phase 3 - Step 18 (final deliverables)

- [x] Final project report (`docs/REPORT.md`)
- [x] Presentation slides (`docs/SLIDES.md` + `docs/Clinical_Lab_Analysis_System.pptx`)
- [x] Demo scenario / walkthrough script (`docs/DEMO.md`)
- [x] Architecture diagram (mermaid in `docs/PLAN.md` and `docs/REPORT.md`)
- [ ] Add the dataset download link in `docs/decisions/decision-log.md` (team to fill)

## Optional / nice-to-have (see `guidelines-gap-analysis.md`)

- [ ] Add a `LICENSE` file
- [ ] Add `pyproject.toml` (build + test/coverage config); optionally adopt `uv`
- [ ] Split `app.py` into smaller UI helper modules

## Ownership

- Data and question design: Hala, Dana
- Architecture, pipeline, UI, tests: Anas, Alon
