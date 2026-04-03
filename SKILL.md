---
name: thinking-clarity
description: Use when the user is stuck, comparing options, overcomplicating a real problem or decision, trying to identify the real bottleneck, or asking things like "what am I missing?", "does this really have to be this way?", "what should I remove?", or "what is the simplest explanation that still fits the facts?"
---

# Thinking Clarity

Turn vague, overloaded, or assumption-heavy problems into clearer judgments and next moves.

## Purpose

Identify the real question, expose key assumptions, reduce the issue into concrete structure, compare simpler options, and end with a recommendation or next move.

## Use When

Use this skill when:

- the user is stuck between meaningful options or directions
- the problem feels vague, overloaded, or overcomplicated
- the user is trying to identify the real bottleneck, dependency, or constraint
- the current explanation has too many assumptions, layers, or moving parts
- the user wants to shrink scope, simplify a plan, or challenge inherited structure
- the task is high-value enough that a clearer judgment would change what happens next

## Do Not Use When

Do not use this skill for:

- simple factual lookup
- purely mechanical execution tasks
- obvious low-risk choices where a direct yes/no or small convention call is enough
- situations where the user clearly wants only a direct conventional answer without reframing
- specific bug debugging, incident triage, traceback chasing, or payload-specific failure analysis where a dedicated debugging workflow should lead
- open-ended ideation where brainstorming is the main job
- cases where the problem framing is already clear and the main work is implementation

## Workflow Routing

- Start with `workflows/clarify.md` when the user is mixing goal, method, fear, or vague language.
- Start with `workflows/deconstruct.md` when the issue is being treated like a black box and the mechanism matters.
- Start with `workflows/simplify.md` when the user already has the rough shape but needs to remove scope, steps, or assumptions.
- Start with `workflows/decide.md` when the issue is already clear enough that the main need is a recommendation, decision rule, or next move.

Routing notes:

- Do not skip `clarify` when the user is naming a solution, team shape, architecture move, or status signal as if it were the problem.
- Do not skip `deconstruct` when the answer depends on distinguishing root cause from symptom, mechanism from narrative, or hard limits from softer pressure.
- `simplify` is often enough when the real goal and option set are already explicit and the main job is finding the smallest sufficient path.
- Go straight to `decide` when the user has already named the real bottleneck, remaining options, or decision criterion and is explicitly asking what to do first.
- Do not reopen upstream analysis just to sound careful if the frame is already decision-ready.
- Add `decide` as soon as a working judgment is possible. Do not hold back a recommendation just because earlier workflow stages were used.
- If you're unsure which entry point fits, start with `clarify`.

Use the full sequence `clarify -> deconstruct -> simplify -> decide` only when each step is still earning its keep. Do not force all four stages by default.

`Pressure Test` is a response mode, not a separate workflow. When the user wants an existing proposal, explanation, or plan challenged, keep the workflow based on problem shape and apply `Pressure Test` as the output mode. Do not switch to `Pressure Test` just because the prompt quotes a belief, leadership opinion, or inherited claim. If the real job is choosing scope, priority, sequencing, or the smallest viable path under constraints, prefer `Structured Analysis`.

## Response Modes

- Quick Reframe: use when one framing problem is blocking progress and the user mainly needs a narrower question plus an immediate next move. If you are already comparing facts, interventions, or tradeoffs, this is no longer the right mode.
- Structured Analysis: use when multiple facts, constraints, tradeoffs, or options need to be made explicit before choosing a direction. This is the default mode for scope, sequencing, architecture, and prioritization decisions, even when a claim appears in the background.
- Pressure Test: use when the answer should be centered on whether a specific claim, proposal, explanation, or plan survives scrutiny. The answer should revolve around assumptions, missing evidence, contradiction, and what still holds.

Mode choice should change the answer shape, not just the label.

## Output Contract

Every triggered response should leave the user with four things, even if labels vary:

- a clearer problem frame
- the decision-relevant facts and constraints
- a working judgment
- an immediate next move

Recommended structured slots by mode:

- Quick Reframe: `surface question`, `real goal`, `framing problem`, `reframed question`, `next move`
- Structured Analysis: `real goal`, `decision-relevant facts`, `hard constraints`, `soft constraints`, `options or moving parts`, `recommendation`, `next move`
- Pressure Test: `claim under test`, `weak assumptions`, `missing evidence or contradiction`, `what survives scrutiny`, `recommendation`, `next move`

Additional contract rules:

- If the primary workflow includes `deconstruct`, make `components` and `causal structure` explicit unless they are genuinely trivial.
- If the answer contains a working recommendation based on facts, constraints, or compared interventions, do not label it `Quick Reframe`.
- If the answer is organized around scope, priority, or sequencing under constraints, do not label it `Pressure Test` unless claim scrutiny is the actual center of gravity.
- If the prompt is really a direct debugging request or a trivial low-risk choice, do not force this output contract onto it.
- If the prompt is a low-risk convention call, prefer the safe direct default over asking for more context.
- For trivial readability or naming questions, the safe direct default is usually enough: answer the yes/no, give one short reason, and stop.

When the judgment depends on uncertain premises, make those dependencies explicit instead of pretending the answer is firmer than it is.

## Required Rules

1. Clarify before solving.
2. Do not treat soft constraints as fixed without justification.
3. Prefer mechanism over narrative.
4. Simplicity must preserve adequacy.
5. Do not end with reflection alone; end with a recommendation, rule, or next step.
6. Stop the workflow as soon as the answer is clear enough to act on.
7. Do not let a quoted claim or internal opinion automatically force `Pressure Test`.
8. If you choose `deconstruct`, show the structure explicitly rather than jumping straight to recommendation.
9. Do not steal direct debugging prompts, trivial choices, or explicit conventional-answer requests just because they contain analytical language.
10. If the frame is already decision-ready but some detail is missing, give the best provisional recommendation or decision rule you can instead of stopping at "need more information."
11. If you trigger on a decision-ready prompt, include `Main tradeoff or risk:` and `Next move:` explicitly. Do not stop at a bare recommendation.

## When Information Is Incomplete

If information is incomplete:

1. name the key ambiguity
2. state the minimum necessary assumptions
3. continue with the best current interpretation
4. say what fact would most change the recommendation
5. still give the best current move unless doing so would require inventing facts

For low-risk convention calls, do not turn missing context into a workflow trigger. Use the direct safe default unless the user has clearly signaled unusual stakes.

For decision-ready prompts with incomplete option detail, do not ask for the missing list as the whole answer. Give the best current decision rule, state the main tradeoff, and say what missing fact would most change the recommendation.

## References

Read only references that are both relevant to the current task and available in this skill:

- `references/anti-patterns.md` when the reasoning starts getting abstract, contrarian, or non-actionable
- `references/output-patterns.md` when choosing the output shape
- `references/examples.md` when calibrating tone, scope, or answer structure
