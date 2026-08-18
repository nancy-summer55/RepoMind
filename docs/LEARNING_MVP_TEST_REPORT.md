# Learning MVP Test Report

Test date: 2026-08-18

## Test Scope

This report covers final acceptance for the current RepoMind Learning MVP based on:

- README positioning and documented behavior
- Demo / User / Developer / Release checklist documents
- Learning evaluation assets in `evaluation/`
- Automated Python test suite
- Local runtime environment checks for launching the Streamlit app

The goal was to verify, when possible:

- repository indexing flow
- Learning Map availability
- starter questions and follow-ups
- feature / concept / configuration / refusal answer paths
- source inspector and retrieval debug visibility

## Environment

- OS context: Windows workspace under `<project_root>`
- Date: 2026-08-18
- Python used for automated checks: `<python_executable>`
- Python version: `3.13.15`
- Repository working tree state at test start:

```text
 M README.md
 M app.py
 M ui/components.py
?? RepoMind_Demo_Script.md
?? RepoMind_Dev_Setup.md
?? RepoMind_Release_Checklist.md
?? RepoMind_User_Guide.md
?? docs/IMPLEMENTATION_BASELINE.md
?? evaluation/learning_eval_questions.json
?? evaluation/learning_eval_template.md
?? learning/
?? tests/
```

Observed local environment constraints:

- `.env` file was not present in the repository root.
- `streamlit` was not installed in `<python_executable>`.
- `openai` was not installed in `<python_executable>`.
- No local nanoGPT repository directory was discovered under `<workspace_root>`; only evaluation assets referencing nanoGPT were present.
- No usable local virtual environment directory (`.venv`, `venv`, `env`) was detected in the repository root.

## Automated Checks

### 1. Pytest

Command:

```text
<python_executable> -m pytest -q
```

Result:

- Passed
- `120 passed in 0.18s`

Assessment:

- Verified passed

### 2. Compileall

Command:

```text
<python_executable> -m compileall learning app.py ui
```

Result:

- Passed
- `learning/`, `app.py`, and `ui/` compiled without reported syntax errors

Assessment:

- Verified passed

## Manual Validation

### 1. Streamlit launch attempt

Commands attempted:

```text
where.exe streamlit
streamlit run app.py --server.headless true
<python_executable> -m streamlit --version
<python_executable> -m pip show streamlit
```

Observed result:

- `streamlit` command was not found
- `<python_executable> -m streamlit --version` failed with `No module named streamlit`
- `pip show streamlit` reported package not found

Assessment:

- Blocking issue for local UI validation in the tested interpreter

### 2. DeepSeek environment readiness

Checks performed:

```text
Test-Path .env
<python_executable> -m pip show openai
```

Observed result:

- `.env` missing
- `openai` package missing in the tested interpreter

Assessment:

- Blocking issue for Learning Map generation and Guided Q&A generation in the tested interpreter

### 3. Local demo repository readiness

Check performed:

```text
rg --files <workspace_root> | rg "nanoGPT|nanogpt"
```

Observed result:

- Only evaluation assets under `<project_root>\evaluation\...` were found
- No local nanoGPT code repository path was discovered

Assessment:

- Blocking issue for real indexing / end-to-end repository validation on this machine state

## Validated Flows

### Verified passed

- Learning package schema / metadata / map / pipeline / generator / adapter / intent / planner / composer / follow-up / source label / guided Q&A tests all passed through the full pytest suite.
- `app.py`, `learning/`, and `ui/` passed Python compilation checks.
- Evaluation assets exist:
  - `evaluation/learning_eval_questions.json`
  - `evaluation/learning_eval_template.md`
- Product / demo / user / dev / release documents exist and align at the feature-description level.

### Environment prevented validation

- Repository indexing flow in the live app
- Learning Map appearing in the live UI
- Starter question click-through in the live UI
- Follow-up click-through in the live UI
- Feature question answer path in the live UI
- Concept question answer path in the live UI
- Configuration question answer path in the live UI
- Refusal path in the live UI
- Source inspector rendering in the live UI
- Retrieval debug rendering in the live UI

### Found issue but non-blocking for code correctness

- Working tree is not clean; there are existing modified and untracked files.
- Several documentation files showed mojibake / encoding artifacts when printed in the current terminal session. This does not prove file corruption, but it is a share-risk for documentation readability.

### Found blocking issues

- `streamlit` is not installed in the tested Python environment.
- `openai` is not installed in the tested Python environment.
- `.env` is missing, so no DeepSeek API key is configured.
- No local nanoGPT repository was available for real indexing validation.

## Blockers / Gaps

1. UI runtime could not be launched from the tested interpreter because `streamlit` was not installed.
2. LLM-backed flows could not be exercised because `.env` was missing and `openai` was not installed.
3. End-to-end indexing could not be validated because no local nanoGPT repository path was available.
4. Because of the three blockers above, the final acceptance could not verify the release checklist items that depend on a live app session.

## Known Risks

- Release readiness currently depends more on automated tests and prior implementation work than on fresh live end-to-end execution in this environment.
- Symbol-level retrieval is a known product risk and is already documented as weaker than file-level retrieval.
- BM25 is rebuilt per query, which may become a performance issue on larger repositories.
- Learning Map generation is fail-open by design; this is good for availability, but it means indexing success does not guarantee Learning Map success.
- Documentation encoding / terminal rendering issues may reduce sharing quality if not checked in the target viewing environment.

## Release Readiness Recommendation

Current recommendation: conditionally ready for code sharing and internal demo preparation, but not fully ready for final external "verified runnable" release from this machine state.

Reasoning:

- The codebase passed automated tests and compile checks.
- The Learning MVP artifact set is present: documentation, evaluation dataset, manual evaluation template, demo script, user guide, developer setup guide, and release checklist.
- However, this environment did not satisfy the minimum runtime prerequisites for a live final acceptance:
  - missing `streamlit`
  - missing `openai`
  - missing `.env`
  - missing local demo repository

Recommended next step before calling it fully release-verified:

1. Install runtime dependencies from `requirements.txt` into the actual interpreter used for launch.
2. Create `.env` with a valid `DEEPSEEK_API_KEY`.
3. Prepare a local nanoGPT repository path.
4. Re-run a short live acceptance covering index, Learning Map, starter question, one feature question, one concept question, one refusal question, source inspector, and retrieval debug.
