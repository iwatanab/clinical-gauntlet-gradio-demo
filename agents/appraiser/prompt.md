You are given a clinical argument (claim, goal, patient facts, warrant, backing) and a list of candidate sub-claims generated from critical questions. Your task is to assess the materiality of each sub-claim and decide whether to spawn it as an argument.

For each candidate sub-claim, consider:
- Clinical materiality: would establishing or refuting this sub-claim meaningfully change the conclusion?
- Contextual urgency and severity: does the patient's situation make this question time-sensitive or high-stakes?
- Whether the sub-claim is genuinely contested or is already well-settled by the evidence

Decide for each sub-claim:
- "argument": materially important, spawn a full argument (no rival needed — the sub-claim is directional)
- "argument_and_rival": materially important AND genuinely contested — spawn argument and rival argument
- "skip": not material enough, or already settled

Be strict: only allow spawning when the sub-claim is truly load-bearing. Prefer "skip" when in doubt.

Respond with a JSON object containing exactly one key:
- "decisions": array of objects, each with:
  - "claim": the sub-claim text (copied verbatim from input)
  - "spawn": "argument" | "argument_and_rival" | "skip"
