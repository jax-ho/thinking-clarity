# Scripts Usage

This directory contains repository-level validation and evaluation entry points for the `thinking-clarity` skill.

These scripts are not part of the installable skill package. The package lives at `skills/thinking-clarity/`; the scripts read that folder as their skill source.

## What Each Script Does

### `quick_validate.py`

Static validation for the repo contract.

Checks:
- documentation contract
- contract case schema and coverage
- trigger case schema and coverage

Use this first after any content edit.

Command:

```bash
uv run python scripts/quick_validate.py
```

### `run_eval.py`

Contract eval.

Purpose:
- test whether the skill materials produce the expected `should_trigger / workflow / mode / required fields`
- catch routing drift and output-contract drift

Best used for:
- validating doc-level changes
- checking whether a workflow or mode instruction still holds

Default runner:
- `claude`

Recommended command:

```bash
uv run python scripts/run_eval.py --runner claude --skill-environment isolated --claude-effort medium --bundle-profile balanced
```

Notes:
- `contract eval` is useful, but it is less trustworthy than `trigger eval` for real usability.
- Claude structured output can still be less stable than plain-answer judging. Treat runner errors separately from skill failures.

### `trigger_eval.py`

Real trigger eval.

Purpose:
- test whether the skill actually triggers on a raw prompt
- test whether the resulting answer has the intended effect

This is the most important script for real usability.

Default runner:
- `claude`

Recommended command:

```bash
uv run python scripts/trigger_eval.py --runner claude --skill-environment isolated --answer-reasoning-effort medium --judge-reasoning-effort low
```

Interpretation:
- `expected trigger: True | judged trigger: True` means the answer behaved like the skill triggered
- `expected trigger: False | judged trigger: True` means a false positive
- `missing effects` tells you what quality slot was missing

### `codex_isolation.py`

Environment isolation helpers.

Purpose:
- create isolated `HOME` environments for Codex or Claude
- allow tests to run without pulling in the user's other locally installed skills

Do not use this directly in normal workflow. It is shared support code for the eval scripts.

## Case Files

### `validation_cases.json`

Contract cases for `run_eval.py`.

Use these when you care about:
- workflow choice
- response mode
- required field coverage

### `trigger_cases.json`

Real trigger cases for `trigger_eval.py`.

Use these when you care about:
- whether the skill should win
- whether the final answer actually helps
- whether the skill stays out of the wrong prompts

## Recommended Workflow

When editing the skill:

1. Run static validation.
2. Run targeted trigger eval on the cases most related to your change.
3. Only then run broader trigger eval if needed.
4. Use contract eval as a secondary check, not the primary truth source.

Recommended order:

```bash
uv run python scripts/quick_validate.py
uv run python scripts/trigger_eval.py --runner claude --skill-environment isolated --case <target-case>
uv run python scripts/run_eval.py --runner claude --skill-environment isolated --case <target-case>
```

## High-Value Regression Cases

These are the most useful cases to rerun first after future optimization work:

- `trigger-direct-decide-refactor-choice`
- `non-trigger-obvious-low-risk-choice`
- `non-trigger-debugging-adjacent`
- `trigger-proposal-pressure-test`
- `trigger-platform-team-or-process-fix`

Use them before spending time on full runs.

Example:

```bash
uv run python scripts/trigger_eval.py --runner claude --skill-environment isolated \
  --case trigger-direct-decide-refactor-choice \
  --case non-trigger-obvious-low-risk-choice \
  --case non-trigger-debugging-adjacent
```

## Failure Triage

When a test fails, classify it before editing anything:

### Static validation failure

Likely issue:
- repo contract mismatch
- case schema drift
- missing coverage

Fix location:
- docs, workflows, case files, or validator expectations

### Contract eval failure

Likely issue:
- workflow or mode instructions drifted
- output contract is underspecified
- structured output runner instability

Fix location:
- skill docs first
- runner only if failure is clearly a CLI/schema issue

### Trigger eval failure

Likely issue:
- real trigger boundary drift
- output quality gap
- skill is winning or losing the wrong prompt

Fix location:
- skill docs and examples first
- judge only if the answer is clearly acceptable but the evaluation rubric is too strict

## Current Residual Risk

At the time of this note:
- the scripts are stable enough for future agents to reuse directly
- `trigger_eval.py` is the primary decision tool for real usability
- `run_eval.py` is still useful, but Claude structured output can fail on some cases even when the underlying skill behavior is not the main issue

If a future agent is continuing optimization, they should start from `trigger_eval.py`, not from first principles.
