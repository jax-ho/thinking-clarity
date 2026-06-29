# Examples

Use these examples to calibrate trigger quality, workflow choice, mode choice, and answer shape.

## Triggered Examples

### Example 1: Overbuilt architecture

Primary workflow:
`Simplify -> Decide`

Mode:
`Structured Analysis`

Surface question:
Do we need to split this service right now?

Real goal:
Match architecture to current operational needs without adding coordination cost too early.

Decision-relevant facts:
- current team is small
- operational overhead will increase if services are split
- present bottleneck may still be module boundaries, not deployment topology

Hard constraints:
- no evidence yet of a scaling requirement that forces separate deployables

Soft constraints:
- desire to look mature
- fear of future rework

Options or moving parts:
- keep one deployable, improve internal boundaries
- split only the subsystem with clear operational separation
- split broadly now

Recommendation:
Do not split the full system yet. Strengthen internal boundaries first.

Next move:
Identify one boundary that causes real coupling pain and test whether that pain is operational, organizational, or both.

---

### Example 2: Messy mixed framing

Primary workflow:
`Clarify`

Mode:
`Quick Reframe`

Surface question:
I think we need a better architecture because the codebase feels risky and also we probably need to move faster and maybe split teams soon.

Real goal:
Figure out whether the dominant problem is architecture, team design, or delivery friction.

Framing problem:
Three different worries are being projected onto one architecture decision.

Reframed question:
Which concrete failure pattern are we actually trying to fix first: code coupling, delivery speed, or future team boundaries?

Next move:
List one recent incident for each suspected problem and see which category is real rather than assumed.

---

### Example 3: Agent over-design

Primary workflow:
`Simplify -> Decide`

Mode:
`Structured Analysis`

Surface question:
Should we build a full agent framework now?

Real goal:
Validate whether multi-step tool orchestration is needed before paying framework cost.

Decision-relevant facts:
- the actual workflow is still not validated
- debugging complexity rises sharply with agent layers
- simpler scripted flows are easier to test first

Hard constraints:
- framework work will consume time before proving user value

Soft constraints:
- belief that architecture now will save rework later

Options or moving parts:
- build the framework first
- script one narrow workflow first

Recommendation:
Start with the narrowest workflow that tests the target outcome. Add framework layers only after repeated evidence shows they are needed.

Next move:
Pick one real task, implement it as an explicit scripted flow, and measure whether missing abstractions block iteration.

---

### Example 4: Pressure-testing a proposal

Primary workflow:
`Deconstruct -> Decide`

Mode:
`Pressure Test`

Claim under test:
We need enterprise SSO in the MVP or no serious buyer will talk to us.

Weak assumptions:
- serious buyers evaluate before initial value is demonstrated
- every target buyer requires SSO at first contact
- SSO is the real blocker rather than positioning or workflow fit

Missing evidence or contradiction:
- no lost deal evidence has been named
- buyer conversations may not yet be at procurement depth
- two-week delivery capacity makes SSO expensive relative to current uncertainty

What survives scrutiny:
SSO may become necessary later, but the current claim overstates how early it must exist.

Recommendation:
Do not treat SSO as a hard MVP requirement yet.

Next move:
Ask the next five target buyers where SSO sits in their evaluation sequence and only escalate if it repeatedly blocks early validation.

Why this is `Pressure Test`:
The center of gravity is whether a specific claim survives scrutiny, not broader scope design.

---

### Example 5: Claim inside a broader scope decision

Primary workflow:
`Deconstruct -> Simplify -> Decide`

Mode:
`Structured Analysis`

Surface question:
Leadership says enterprise SSO must be in the MVP because serious buyers expect it, but we only have two weeks. Is that actually required right now?

Real goal:
Choose the smallest credible launch scope that can still validate serious buyer interest.

Decision-relevant facts:
- the delivery window is only two weeks
- the current justification is a generalized buyer belief, not yet named deal evidence
- SSO may matter later in procurement even if it does not block initial evaluation

Hard constraints:
- two weeks of delivery capacity

Soft constraints:
- leadership pressure
- fear of looking non-serious to enterprise buyers

Options or moving parts:
- defer SSO and validate when it actually blocks
- add a workaround for early pilots
- make full SSO a hard MVP requirement now

Recommendation:
Do not treat SSO as a default hard MVP requirement yet. Make it earn its cost with evidence from actual buyer motion.

Next move:
Ask the next five target buyers at what stage SSO becomes mandatory and only escalate if it blocks initial evaluation repeatedly.

Why this is not `Pressure Test`:
There is a claim in the prompt, but the main job is still scope choice under delivery constraints.

---

### Example 6: Org-structure substitution

Primary workflow:
`Clarify -> Deconstruct -> Decide`

Mode:
`Structured Analysis`

Surface question:
People keep saying we need a platform team, but the actual complaints are slow deploys, unclear ownership, and flaky tooling. What problem are we really deciding about?

Real goal:
Decide whether there is one cross-cutting capability gap that needs dedicated ownership or several narrower failures that should be fixed directly.

Reframed question:
Are these symptoms driven by one missing platform function or by separate failures in process, accountability, and tooling quality?

Decision-relevant facts:
- the named complaints are operational failures, not team goals
- a platform team is one intervention, not the underlying problem
- changing team topology before diagnosis can hide distinct causes under one label

Recommendation:
Treat this as a diagnosis decision first and an org-design decision second. Do not form a platform team until you know whether the same capability gap is causing the incidents.

Next move:
Review the last 5 to 10 incidents across deploy slowness, ownership confusion, and tooling flakiness. Identify the recurring cause pattern before deciding on team structure.

---

### Example 7: Problem already clear, go straight to decide

Primary workflow:
`Decide`

Mode:
`Structured Analysis`

Surface question:
We already know review latency is the bottleneck. Three refactor options remain. Which one should we do first?

Real goal:
Choose the first move that reduces review latency fastest without paying for unnecessary refactor scope.

Decision-relevant facts:
- the bottleneck is already named
- the remaining work is option choice, not upstream diagnosis
- reopening architecture analysis would slow the decision without changing it

Recommendation:
Choose the option that shortens review latency directly with the smallest refactor surface first.

Main tradeoff or risk:
This may preserve some structural mess temporarily, but it buys evidence before paying for broader cleanup.

Next move:
Rank the three options by time-to-latency-reduction and pick the fastest credible one this sprint.

If the exact three options are not listed yet:
Still recommend the option class that most directly reduces review latency with the smallest refactor surface, and name the one missing fact that would change the choice. Do not stop at "tell me the options."

Minimum acceptable answer shape here:
- recommendation now
- main tradeoff or risk now
- next move now, explicitly labeled or clearly phrased as the next action
- optional note about the single missing fact that could flip the call

Reference answer shape:

Recommendation:
Start with the refactor that most directly cuts review latency with the smallest implementation surface.

Main tradeoff or risk:
This improves review speed first, but it may leave some deeper structural cleanup for later.

Next move:
Pick the candidate with the shortest time-to-review-latency reduction and start it this sprint.

Minimal three-line template:
`Best current recommendation: Start with the smallest refactor that directly reduces review latency.`
`Main tradeoff or risk: This speeds reviews now but may postpone deeper cleanup.`
`Next move: Choose the option with the fastest time-to-latency reduction and start it this sprint.`

## Non-Triggered Examples

### Example 8: Pure debugging

Prompt:
The API returns 500 on this payload. Where is the bug?

Why this should not trigger:
The main task is root-cause debugging, not problem reframing.

### Example 9: Low-risk convention call

Prompt:
Should I rename this helper method to make it clearer?

Why this should not trigger:
This is an obvious low-risk choice. A direct answer is enough; full analysis would be inflation.

Direct answer shape:
Yes, if the current name is even slightly misleading, rename it to something clearer. This is a low-risk readability improvement, not a decision workflow.

What not to do:
- ask for the file, implementation, and surrounding context before answering
- open a structured analysis with sections
- turn the choice into a broader maintainability or architecture discussion

### Example 10: Pure execution

Prompt:
Rename this variable to `userId` across the file.

Why this should not trigger:
The frame is already clear and the work is mechanical execution.
