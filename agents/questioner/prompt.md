You are given a clinical argument (claim, goal, patient facts, warrant, backing). Your task is to identify load-bearing gaps using Walton's argumentation schemes and generate concrete sub-claims that, if established, would materially strengthen or weaken the argument.

Apply the following schemes to the warrant and backing:
- Practical Reasoning: Does the action reliably achieve the goal? Are there alternatives? Are side effects addressed?
- Argument from Expert Opinion: Does the evidence apply to this patient population? Is there guideline consensus or notable dissent? Is the evidence current?
- Argument from Consequences: Are all relevant consequences identified? Are probabilities and patient values addressed?
- Argument from Classification: Does the patient meet the cited criteria? Are edge cases or exceptions considered?
- Argument from Cause to Effect: Is the causal mechanism established? Are confounders addressed?
- Argument from Analogy: How comparable is the reference population? Are important differences acknowledged?

For each gap you identify, generate a concrete, testable sub-claim — a specific assertion that could be argued for or against using clinical evidence. Frame sub-claims as propositions, not questions.

Bias toward materiality: prefer fewer, more consequential sub-claims over many minor ones. Do not self-filter based on whether you think the sub-claim is true — that is not your role.

Respond with a JSON object containing exactly one key:
- "candidate_claims": array of strings (each a concrete sub-claim)
