# Thinking Clarity

A skill for turning messy, high-value questions into clearer judgments and more executable next moves.

This skill is designed for situations where an agent is at risk of overcomplicating the problem, accepting soft constraints as fixed reality, or producing long analysis without a decision.

## Quick Example

Typical prompts that fit this skill:

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

## Repository Structure

- [SKILL.md](./SKILL.md): main skill contract and routing
- [workflows](./workflows): workflow-specific guidance
- [references](./references): anti-patterns, output shapes, examples
- [scripts](./scripts): validation and evaluation tooling

## Install Locally

If you are developing or editing the skill locally, link the repo into your agent's skills directory.

### Codex

```bash
mkdir -p ~/.codex/skills
ln -s <repo-path> ~/.codex/skills/thinking-clarity
```

### Claude Code

```bash
mkdir -p ~/.claude/skills
ln -s <repo-path> ~/.claude/skills/thinking-clarity
```

Restart the agent after linking.

## Install From GitHub

Once the repo is published, a practical install path is:

```bash
npx skills add <owner>/<repo>
```

If you want users to discover and install the skill more easily, GitHub should be the canonical source.

## Validate

Run static validation first:

```bash
python3 scripts/quick_validate.py
```

Useful next checks:

```bash
python3 scripts/trigger_eval.py --runner claude --skill-environment isolated
python3 scripts/run_eval.py --runner claude --skill-environment isolated
```

More detail is in [scripts/USAGE.md](./scripts/USAGE.md).

## Current Status

The skill is in a shareable state and works well on most high-value trigger cases.

Current known residual risk:

- direct-decision prompts can still occasionally under-express the main tradeoff in real trigger tests, depending on model behavior

## Share It

The practical distribution path is:

1. publish this repo to GitHub
2. verify install from the GitHub URL or repo name
3. share it via `npx skills add ...`
4. let `skills.sh` act as the discovery layer once installs start happening

For public discovery, GitHub is the right first step. `skills.sh` is best treated as a distribution and discovery layer on top of that.
