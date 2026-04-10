You are given the complete recursive argumentation tree for a clinical decision question, serialised as a nested JSON structure. The tree contains a root argument pair (node and rival_node), each with their warrants, backings, citations, arbiter reasoning at each level, and any child argument pairs nested within.

Your task is to synthesise the full tree into a final clinical recommendation.

Steps:
1. Identify the original claim and goal from the root node.
2. Traverse the tree: at each level, read the arbiter_reasoning to understand where the argumentation was resolved and where it was stopped due to insufficient grounds.
3. Weight the evidence: consider the depth at which arguments were stopped, the strength of arbiter verdicts, and whether child arguments resolved or deepened the uncertainty.
4. Produce a nuanced clinical recommendation that:
   - Directly addresses the original claim
   - Names the key factors that favour action and those that counsel caution
   - Identifies uncertainties that remained unresolved in the tree
   - Frames the answer appropriately for clinical risk — do not be falsely decisive when the tree reveals genuine equipoise
   - Does not exceed 4 paragraphs
5. Cite your sources: wherever you draw on a specific guideline, trial, or review to support a statement in the recommendation, cite it inline using the format [Source Name, Year]. Only cite sources that appear in the citations fields of the argument nodes in the tree — do not introduce sources from memory. After the recommendation, include a deduplicated list of all cited sources with their URLs.

Do not reproduce the tree structure. Synthesise it into clinical prose.

Respond with a JSON object containing exactly two keys:
- "recommendation": string (prose with inline citations in the format [Source Name, Year])
- "references": array of objects, each with "source" (string), "url" (string), "year" (string or null), "finding" (string) — include only sources actually cited in the recommendation text, deduplicated
