# Thinking Clarity

A skill for turning messy, high-value questions into clearer judgments and more executable next moves.

Use it when an agent is at risk of overcomplicating the problem, accepting soft constraints as fixed reality, or producing long analysis without a decision.

## Quick Example

Typical prompts that fit:

- "Should we split this service now, or are we solving the wrong problem?"
- "What is the smallest launch scope that still proves this product is real?"
- "Are we treating SSO as a hard requirement when it is really just enterprise inertia?"

## What It Helps With

Use `thinking-clarity` for prompts like:

- architecture or system design tradeoffs
- whether a refactor is worth doing
- MVP scope reduction
- product scope convergence
- AI experiment path selection
- pressure-testing a proposal before committing to it

It is not meant for:

- routine factual lookup
- straightforward debugging
- trivial low-risk choices
- open-ended brainstorming with no decision pressure

## What Good Output Looks Like

When the skill triggers well, the answer should usually:

- identify the real problem instead of the surface framing
- separate hard constraints from soft constraints
- remove unnecessary complexity
- produce a working judgment
- give a recommendation and a next move

## How It Thinks

This skill is built from three classic reasoning moves:

- Socratic questioning: clarify the real problem, the real goal, and any ambiguous terms
- First principles: separate facts, constraints, mechanisms, and dependencies
- Occam's razor: remove unnecessary complexity and prefer the smallest sufficient explanation or move

The point is not to sound deeper. The point is to get from confusion to a clearer judgment faster.

## Install

Install it with the `skills` CLI:

```bash
npx skills add https://github.com/jax-ho/thinking-clarity --skill thinking-clarity
```

The shorter GitHub shorthand also works:

```bash
npx skills add jax-ho/thinking-clarity
```

To inspect the available skill before installing:

```bash
npx skills add https://github.com/jax-ho/thinking-clarity --skill thinking-clarity --list
```

To try the skill without installing it permanently:

```bash
npx skills use https://github.com/jax-ho/thinking-clarity --skill thinking-clarity
```

## Local Development

From a local clone, list the detected skills:

```bash
npx skills add . --skill thinking-clarity --list
```

Install the local working tree:

```bash
npx skills add . --skill thinking-clarity
```

If you specifically want a manual Codex install, copy the skill folder:

```bash
mkdir -p "${CODEX_HOME:-$HOME/.codex}/skills"
cp -R skills/thinking-clarity "${CODEX_HOME:-$HOME/.codex}/skills/thinking-clarity"
```

## Repository Layout

```text
.
├── skills/
│   └── thinking-clarity/
│       ├── SKILL.md
│       ├── agents/
│       │   └── openai.yaml
│       ├── references/
│       │   ├── anti-patterns.md
│       │   ├── examples.md
│       │   └── output-patterns.md
│       └── workflows/
│           ├── clarify.md
│           ├── decide.md
│           ├── deconstruct.md
│           └── simplify.md
├── scripts/
│   ├── quick_validate.py
│   ├── run_eval.py
│   ├── trigger_eval.py
│   └── USAGE.md
├── tests/
│   ├── test_run_eval.py
│   └── test_trigger_eval.py
├── pyproject.toml
└── README.md
```

Only `skills/thinking-clarity/` is the installable skill package. Repository scripts, tests, CI, and Python project files stay outside that folder.

## Skill Package

- [SKILL.md](./skills/thinking-clarity/SKILL.md): main skill contract and routing
- [workflows](./skills/thinking-clarity/workflows): workflow-specific guidance
- [references](./skills/thinking-clarity/references): anti-patterns, output shapes, and examples
- [agents/openai.yaml](./skills/thinking-clarity/agents/openai.yaml): OpenAI-oriented prompt packaging

## Validation

Run static validation first:

```bash
uv run python scripts/quick_validate.py
```

Run unit tests:

```bash
uv run pytest
```

The same checks can also be run with system Python when dependencies are already available:

```bash
python3 scripts/quick_validate.py
python3 -m pytest tests/ -v
```

Useful next eval checks:

```bash
uv run python scripts/trigger_eval.py --runner claude --skill-environment isolated
uv run python scripts/run_eval.py --runner claude --skill-environment isolated
```

More detail is in [scripts/USAGE.md](./scripts/USAGE.md).

## Evaluation

Use `trigger_eval.py` as the primary usability signal. It checks whether the skill actually wins the right prompts and stays out of the wrong ones.

Use `run_eval.py` as a contract check for workflow choice, response mode, and required fields.

## Current Status

The skill is in a shareable state and works well on most high-value trigger cases.

Current known residual risk:

- direct-decision prompts can still occasionally under-express the main tradeoff in real trigger tests, depending on model behavior
