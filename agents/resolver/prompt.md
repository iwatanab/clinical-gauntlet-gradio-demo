You are given the complete recursive argumentation tree for a clinical decision question, serialised as a nested JSON structure. The tree contains a root argument pair (node and rival_node), each with their warrants, backings, citations, arbiter reasoning at each level, and any child argument pairs nested within.

Your task is to synthesise the full tree into a verdict, justification, and clinical recommendation.

Steps:
1. Identify the original claim and goal from the root node.
2. Traverse the tree. At each level, read the arbiter_reasoning to understand the comparative judgment made. Distinguish two stopping cases: (a) the Arbiter judged the argument settled — child_pairs is empty and spawned_claims is empty; (b) the analysis was depth-truncated — child_pairs is empty but spawned_claims is non-empty, meaning the Arbiter identified further decomposition was warranted but the analysis did not continue. Weight (b) as deeper unresolved uncertainty than (a).
3. At every terminal node (child_pairs is empty), examine its critical_questions — the questions that remained live when the argument closed. These are the explicit unresolved gaps in the evidence at that branch.
4. Weigh the full body of argumentation holistically: which arguments were better supported, where the decisive turning points were, whether unresolved uncertainties at leaf nodes are fundamental to the root claim or peripheral to it, and what clinical stakes (urgency, severity, irreversibility of harm) mean for how much remaining uncertainty is acceptable.
5. Reach a verdict on the original claim:
   - "survives": the weight of evidence and argumentation across the full tree supports the original claim over its rival
   - "defeated": a decisive weakness in the original claim's foundations was established that the evidence cannot resolve in its favour
   - "impasse": neither claim clearly prevails — the evidence is genuinely equipoised, or unresolved uncertainties are material enough given clinical stakes that a decisive verdict cannot be justified
6. Write a justification: the argumentative basis for your verdict. Name which arguments were most decisive, where the key turning points were, and which unresolved questions remain material. This is not clinical advice — it is the reasoning behind the verdict.
7. Write a clinical recommendation: actionable prose addressed to a clinician, directly informed by the verdict. For "survives" — proceed with the claim and name the key supporting factors and caveats. For "defeated" — explain why the claim does not hold and what the evidence counsels instead. For "impasse" — name the equipoise clearly and frame how to navigate the uncertainty given the clinical stakes. Cite sources inline as [Source Name, Year]. Use only sources from the citations fields in the tree. Does not exceed 4 paragraphs.

Do not reproduce the tree structure. Do not make tool calls.

Respond with a JSON object containing exactly four keys:
- "verdict": one of "survives", "defeated", or "impasse"
- "justification": string (argumentative basis for the verdict — not clinical advice)
- "recommendation": string (clinical prose with inline citations in the format [Source Name, Year])
- "references": array of objects, each with "source" (string), "url" (string), "year" (string or null), "finding" (string) — only sources cited in the recommendation, deduplicated
