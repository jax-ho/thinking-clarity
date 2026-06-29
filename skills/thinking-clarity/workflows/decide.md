# Decide Workflow

Use this workflow to convert clarified, decomposed, and simplified reasoning into a practical judgment or next move.

## When to use

Use this workflow when:

- the user needs a recommendation
- multiple options remain
- the issue is clearer but still unresolved
- the real bottleneck or decision criterion is already named
- the user explicitly wants the one option, order, or move they should choose first
- analysis must become action
- the conversation risks ending in abstract reflection

## Core question

Given the clarified problem, real facts, and simplified options, what is the best current move?

If the frame is already clear enough to choose, do not reopen `clarify` or `deconstruct` just to restate what the user already knows.

## Process

### Step 1: Keep only what survived scrutiny

Retain only:

- the real goal
- supported facts
- hard constraints
- lower-assumption options
- relevant tradeoffs

### Step 2: Remove what did not survive

Discard:

- vague framing
- unsupported assumptions
- inherited but challengeable defaults
- complexity without clear value
- weak options that only look complete

### Step 3: State the best current judgment

Produce one of:

- a recommendation
- a priority order
- a preferred option
- a decision rule
- a cleaner framing of the remaining choice

If some detail is still missing but the decision criterion is already clear, give the best provisional recommendation or decision rule anyway. Name the missing fact that would change it, but do not stop at information collection.

Bad Decide pattern:
List the options and I'll tell you later.

Correct Decide pattern:
State the best current recommendation or ranking rule now, then name the one missing fact that would most change it.

### Step 4: Name the main tradeoff or risk

Be explicit about what is being sacrificed, accepted, or still uncertain.

For decision-ready prompts, write this as an explicit line:
`Main tradeoff or risk: ...`

### Step 5: End with an immediate next move

Give:

- a first action
- a smallest useful experiment
- a validation step
- a question that must be answered next

For decision-ready prompts, this should usually be one explicit sentence such as:
- "Next move: do X this sprint."
- "Next move: rank Y by criterion Z and start with the top one."
- "Next move: validate the call by checking fact Q."

Do not imply the next move. Write it explicitly as:
`Next move: ...`

## Handoff rule

If no recommendation can be made without inventing facts, return the blocking uncertainty and the next fact to resolve. If the question is still fuzzy, go back to `workflows/clarify.md`. If the structure is still opaque, go back to `workflows/deconstruct.md`. If the option set is still bloated, go back to `workflows/simplify.md`.

Do not use this workflow as an excuse to bounce low-risk convention calls back into more analysis. If the choice is trivial and safe, answer directly instead of escalating.

If the user asks a trivial naming or readability question, do not convert it into a structured decision workflow. Give the direct default answer unless unusual risk has been stated.

## Output format

- what is now clear
- what still matters
- best current recommendation
- main tradeoff or risk
- next move

For decision-ready prompts, the minimum acceptable ending is:
- `Best current recommendation: ...`
- `Main tradeoff or risk: ...`
- `Next move: ...`

## Quality bar

A good decision output should feel more decisive, more grounded, and more usable than the original discussion. It should close analysis debt, not reopen it. If the recommendation depends on a claim under test, a hidden mechanism, or an unresolved framing problem, route back and make that explicit instead of faking certainty.

It should also stay proportionate. If the user already knows the bottleneck and is asking what to do first, answer that question directly with the smallest amount of structure needed to make the choice usable.
