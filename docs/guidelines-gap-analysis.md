# Guidelines Gap Analysis

This page maps the project against common professional software-engineering
practices (documentation, testing, modularity, configuration, and UX). These
are used here as **inspiration**, not a binding rubric.

## Already in place

- **README.md** at the root with install, usage, supported questions, and
  "adding a question" instructions.
- **`docs/` folder** with plans, a decision/progress log, this gap analysis,
  and a test report.
- **Modular structure** with a clear separation of concerns
  (`data_prep`, `questions`, `code_generation`, `execution`, `validation`,
  `correction`, `result_presentation`, `main_pipeline`, `app`).
- **Single source of truth** for questions via a config-driven registry.
- **Tests + coverage**: 56 tests, 94% line coverage (target 85%), including a
  per-question end-to-end test and documented expected results (see
  `TEST_REPORT.md`).
- **Edge cases & graceful degradation**: no-records banner, correction loop,
  empty/invalid handling.
- **Docstrings** on modules/functions; comments explain intent.
- **Config separated from code**: dark theme in `.streamlit/config.toml`.
- **Version control**: clear commit history, dataset kept out of git with a
  documented retrieval path.
- **UX**: status visibility, readable result/validation/code tabs, clear error
  and empty states (aligns with several Nielsen heuristics).

## Optional / not applicable for this project

- **SDK layer + API Gatekeeper + rate limiting** — designed for systems that
  call external/LLM APIs. This MVP uses only a local dataset and template-based
  code generation, so there are no external API calls to gate.
- **`uv` package manager** — the project currently uses `pip` + `requirements.txt`.
  Migrating to `uv`/`pyproject.toml` is straightforward if required.
- **150-line file cap** — most files comply; `app.py` is larger because it is the
  UI layer. It could be split into UI helper modules if strictly required.
- **Formal `PRD.md` / `PLAN.md` / `TODO.md`** — equivalents exist under
  `docs/plans/` and `docs/decisions/`; these could be renamed/expanded to match.
- **Cost/token analysis** — not applicable (no paid API usage at runtime).

## Suggested next steps (if pursuing full compliance)

1. Add `pyproject.toml` (build + pytest/coverage config) and adopt `uv`.
2. Rename/expand docs to `PRD.md`, `PLAN.md`, `TODO.md`.
3. Split `app.py` into smaller UI modules if the 150-line cap is required.
4. Add a `LICENSE` and a short architecture diagram to the docs.
