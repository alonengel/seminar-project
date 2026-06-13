# Decision & Progress Log

A running log of decisions and progress for the Clinical Lab Analysis System (seminar project).
Newest entries at the top.

## 2026-06-13

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
- Base files and plan/docs committed to git and pushed to `origin`.
- Step 17 implementation not started yet (awaiting go-ahead).
