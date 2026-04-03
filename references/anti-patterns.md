# Anti-Patterns

Use this file to avoid turning thinking clarity into abstract, bloated, or misleading reasoning.

## Core warning

This skill should not become:

- endless questioning
- false depth
- false simplicity
- contrarian theater
- analysis without action
- recommendation theater
- full-sequence theater

The goal is better judgment, not more intellectual performance.

## Common failure modes

### 1. Endless questioning

Main risk stage:
Clarify

Bad pattern:
Asking more questions without making the problem clearer.

Correction:
Ask only the questions that materially improve the framing or decision.

### 2. Solving the wrong question well

Main risk stage:
Clarify

Bad pattern:
Accepting the user's framing without checking whether it is the real issue.

Correction:
Clarify the actual goal before analyzing solutions.

### 3. Abstract decomposition

Main risk stage:
Deconstruct

Bad pattern:
Talking about fundamentals without naming actual facts, constraints, costs, incentives, or mechanisms.

Correction:
Reduce the problem into concrete parts.

### 4. False simplicity

Main risk stage:
Simplify

Bad pattern:
Removing complexity by ignoring important evidence or constraints.

Correction:
Simplify must preserve adequacy.

### 5. Soft-constraint hardening

Main risk stage:
Deconstruct / Decide

Bad pattern:
Treating preferences, defaults, or internal politics as if they were hard boundaries.

Correction:
Separate hard constraints from soft constraints before recommending a path.

### 6. Contrarian theater

Main risk stage:
Clarify / Simplify

Bad pattern:
Rejecting conventions automatically because they are conventional.

Correction:
Reject only what fails scrutiny or necessity.

### 7. Recommendation theater

Main risk stage:
Decide

Bad pattern:
The answer sounds smart but leaves the user with no clearer move.

Correction:
Always end with a recommendation, next step, validation move, or decision rule.

### 8. Full-sequence theater

Main risk stage:
Routing

Bad pattern:
Running `Clarify -> Deconstruct -> Simplify -> Decide` by default even when one lighter route would do.

Correction:
Start from the current blockage and stop as soon as the answer is clear enough to act on.

### 9. Mode drift

Main risk stage:
All stages

Bad pattern:
Using `Quick Reframe`, `Structured Analysis`, and `Pressure Test` as cosmetic labels while the answer shape stays the same.

Correction:
Let mode choice change what is emphasized, what is omitted, and how directly the answer moves toward action.

### 10. Routing compression

Main risk stage:
Routing

Bad pattern:
Skipping `clarify` or `deconstruct` just because a shorter answer sounds cleaner, even though the recommendation depends on identifying the real problem or mechanism first.

Correction:
Use the lightest route that still preserves the reasoning needed for a sound judgment. Shorter is not better if it changes what the answer should be about.

### 11. Pressure-test overreach

Main risk stage:
Mode choice

Bad pattern:
Switching to `Pressure Test` whenever the prompt quotes a belief, leadership opinion, or inherited claim, even when the actual job is choosing scope, sequence, or direction under constraints.

Correction:
Use `Pressure Test` only when the answer should be organized around whether the claim survives scrutiny. Otherwise, prefer `Structured Analysis`.

### 12. Boundary theft

Main risk stage:
Triggering

Bad pattern:
Stealing prompts that are really direct debugging, trivial convention calls, or explicit conventional-answer requests because they contain words like "think", "cleanest", or "what's the best way".

Correction:
Judge the real job, not the surface phrasing. If the user mainly needs debugging steps, a small yes/no convention call, or a conventional summary without reframing, stay out.

### 13. Decision reopening

Main risk stage:
Decide

Bad pattern:
The user has already named the bottleneck and remaining options, but the answer reopens upstream framing or decomposition instead of choosing.

Correction:
When the frame is already decision-ready, go straight to the recommendation, name the main tradeoff, and end with the next move.

Do not collapse into "I need more information" when a provisional recommendation or decision rule is already possible.

### 14. Safe-default inflation

Main risk stage:
Triggering / Decide

Bad pattern:
Treating a trivial naming, readability, or convention question as if it needs a full analysis pass or more context gathering before any answer is possible.

Correction:
If the user is asking a low-risk convention call, use the safe direct default. One short reason is enough. Do not escalate unless unusual stakes are explicit.

## Self-check before finalizing

Ask:

- Did I identify the real question?
- Did I expose the main assumption?
- Did I separate facts from narrative?
- Did I challenge soft constraints that shape the recommendation?
- Did I simplify without deleting reality?
- Did I end with a useful next move?

If any answer is no, revise.
