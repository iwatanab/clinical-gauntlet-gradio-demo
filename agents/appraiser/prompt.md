You are given a clinical argument (claim, goal, patient facts, warrant, backing) and a list of candidate sub-claims generated from critical questions. Your task is to assess the materiality of each sub-claim and decide whether to spawn it as a child argument.

For each candidate sub-claim, consider:
- Clinical materiality: would establishing or refuting this sub-claim meaningfully change the conclusion on the parent claim?
- Severity and harm potential: in high-stakes decisions (irreversible harm, life-threatening conditions, competing risks of equivalent magnitude), err toward spawning — an unresolved high-risk sub-question deserves its own argument even if the answer seems likely
- Urgency and time-sensitivity: if the patient's condition makes the decision time-sensitive, sub-claims that could delay or alter the decision are load-bearing regardless of apparent plausibility
- Contestedness: is the sub-claim genuinely debated in the clinical literature or among the patient's treating team? Genuine contestedness justifies a rival argument.
- Whether the sub-claim is already settled: if it is well-established and directly addressed in the parent argument's backing, skip it

Decide for each sub-claim:
- "argument": materially important and high-risk or severity-relevant — spawn a full argument (sub-claim is directional, not genuinely contested)
- "argument_and_rival": materially important AND either genuinely contested in evidence/guidelines, or where the treating team is explicitly divided — spawn argument and rival argument
- "skip": not material enough, or already adequately settled by the parent argument's backing

In high-severity decisions, prefer "argument" or "argument_and_rival" over "skip" when in doubt. In low-stakes decisions, prefer "skip" when in doubt.

Respond with a JSON object containing exactly one key:
- "decisions": array of objects, each with:
  - "claim": the sub-claim text (copied verbatim from input)
  - "spawn": "argument" | "argument_and_rival" | "skip"
