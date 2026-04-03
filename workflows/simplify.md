# Simplify Workflow

Use this workflow to reduce unnecessary complexity while preserving adequacy.

## When to use

Use this workflow when:

- there are too many options
- the proposed solution feels overbuilt
- the explanation has too many assumptions
- the workflow contains too many steps
- the system has too many moving parts
- the user asks what can be removed

## Core question

What is the simplest path, explanation, or design that still works?

## Process

### Step 1: Define adequacy

State the minimum thing the explanation or system must still do.

### Step 2: List current options or moving parts

Make the competing explanations, features, steps, or structures explicit.

### Step 3: Measure assumption load

For each option or component, ask:

- how many extra assumptions it requires
- how many dependencies it adds
- how many actors or handoffs it introduces
- whether it exists for a real function or just reassurance

### Step 4: Remove non-essential complexity

Prefer removing:

- decorative complexity
- speculative additions
- duplicate layers
- workaround-driven structure
- optional steps with low payoff

### Step 5: Compare simplified candidates

Prefer the option that:

- still fits the facts
- still satisfies the real goal
- uses fewer assumptions
- adds less coordination cost
- is easier to test or execute

### Step 6: State what would justify more complexity later

Name the evidence or condition that would force a more complex path.

## Handoff rule

Stop once one candidate is clearly sufficient under the adequacy test and further simplification would remove necessary capability. If a final choice is now possible, move to `workflows/decide.md`

## Output format

- what must be preserved
- current options or moving parts
- assumption load
- what can be removed
- simplest sufficient option
- recommendation
- next move
- what would justify more complexity later

## Quality bar

A good simplification should feel cleaner and more direct without deleting real constraints. When one option is already clearly sufficient, say so and end with the next move instead of stopping at comparison.
