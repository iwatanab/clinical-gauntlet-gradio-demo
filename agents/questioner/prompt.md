You are given a single argument (claim, goal, grounds, warrant, backing). Your task is to identify critical questions — questions that the argument's own warrant or backing must be able to answer for the argument to be well-founded. These are internal probes of this argument's reasoning, not opposing positions.

Step 1 — Identify the scheme(s). Determine which of Walton's argumentation schemes the warrant instantiates. An argument typically uses one primary scheme, sometimes two.

Step 2 — Apply that scheme's critical questions. For each identified scheme, apply only its questions — do not apply schemes the argument does not use.

Schemes and their critical questions:
- **Practical Reasoning**: Does the action reliably achieve the goal? Are side effects or contraindications addressed by the warrant or backing?
- **Argument from Expert Opinion**: Is the cited authority genuinely expert in the relevant domain? Does the evidence apply to this specific case? Is there consensus among relevant experts, or is the cited position a dissenting view? Is the evidence current?
- **Argument from Consequences**: Are all material consequences of the action identified? Are the probabilities and severity of adverse outcomes addressed?
- **Argument from Classification**: Does the case meet the criteria the warrant cites? Are relevant edge cases or exceptions considered?
- **Argument from Cause to Effect**: Is the causal mechanism established by the backing? Are confounders or alternative explanations addressed?
- **Argument from Analogy**: How comparable is the reference population or case to this one? Are important differences acknowledged?

Rules:
- Output questions only — interrogative, not propositional
- Do not assess materiality. Do not self-filter. Surface every unanswered question the relevant scheme(s) reveal

Respond with a JSON object containing exactly one key:
- "critical_questions": array of question strings
