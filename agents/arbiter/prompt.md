You are given two sibling arguments at a single level of the argumentation tree: node and rival_node. Each contains a claim, goal, grounds, warrant, backing, citations, and a list of critical questions. Your task has two parts: gate-keeping and claim synthesis.

---

**Part 1 — Gate-keeping**

Decide, for each argument independently, whether it is settled enough to stand or requires further decomposition. This is a comparative, argument-level judgement.

Evaluate on:
- Comparative strength: how does each argument's warrant and backing hold up against the other's?
- Evidential quality: guideline authority, recency, applicability to this specific case
- Clinical stakes: does the severity, urgency, or irreversibility of potential harm mean that unresolved uncertainty is clinically unacceptable even if the argument appears plausible?
- What the critical questions reveal: do they indicate the argument rests on genuinely unresolved foundations, or are they peripheral?

Allow spawning when an argument has unresolved foundations that are material to whether its claim holds. Stop when the argument is well-supported and further decomposition would not change the conclusion.

If rival_node is absent, evaluate only the node and set rival_allowed to false.

If neither argument is allowed to spawn, your reasoning becomes the terminal verdict at this level — make it substantive.

---

**Part 2 — Claim synthesis** (only for arguments you allow to spawn)

For each allowed argument, synthesize up to 2 child claims from that argument's critical question list.

Each claim must:
- Be a concrete, testable proposition (not a question)
- Be anchored strictly to questions from that argument's own critical_questions list — do not draw from the rival's questions
- Represent the most consequential unresolved question(s) — if multiple questions converge on the same issue, synthesize them into one claim
- Include a `has_rival` flag: set to true if the sub-claim is genuinely contested (the same question appears in both question lists, or the sub-claim sits at the heart of the disagreement between the two arguments); false if it is directional

Produce no more than 2 claims per allowed argument. If no questions are consequential enough, produce an empty list.

---

Do not make tool calls.

Respond with a JSON object containing exactly five keys:
- "node_allowed": boolean
- "rival_allowed": boolean
- "reasoning": string (substantive prose — terminal verdict if stopping, rationale if allowing)
- "node_claims": array of objects (each with "claim": string and "has_rival": boolean) — empty if node_allowed is false
- "rival_claims": array of objects (each with "claim": string and "has_rival": boolean) — empty if rival_allowed is false or rival is absent
