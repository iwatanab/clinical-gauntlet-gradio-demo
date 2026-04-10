Construct a Toulmin-structured argument in favour of the claim provided, using evidence retrieved from the web. The goal defines the clinical objective the claim is intended to achieve — keep it in view throughout to ensure the warrant and backing remain purposefully directed toward that outcome.

Steps:
1. Extract verbatim from the patient facts only the facts that directly support the claim being argued. Use only these quoted facts — do not paraphrase, do not supplement with external knowledge.
2. Use `web_search` to construct the warrant and backing only. Searches should target evidence that connects the patient facts to the goal via the claim. Ground every statement exclusively in:
   - Authoritative clinical guidelines (ACC/AHA, ADA, USPSTF, AAFP, ESC, and relevant society guidelines)
   - Cochrane systematic reviews and meta-analyses
   - Landmark randomised controlled trials (RCTs)
   Make multiple targeted searches as needed — by guideline name, organisation, and year.
3. Construct:
   - **Warrant**: The clinical principle or guideline recommendation that bridges the patient facts to the claim — the rule that licenses the inference.
   - **Backing**: The specific guidelines, reviews, or trials that support the warrant. Name each source: organisation, title, year, and the precise recommendation or finding it contributes.
   - **Citations**: For every source named in the backing, record its full provenance as a structured citation. Each citation must include the source name, the URL retrieved, the publication year, and the specific finding or recommendation used. Do not cite sources that were not retrieved via web_search.

Do not assert facts from memory. Every clinical statement must be traceable to a retrieved source.

If the claim is practical, support or reject the action in light of the goal and consider contraindications/exclusions, harmful consequences, prior failure, and alternative actions for the same goal; if the claim is epistemic, support or reject the explanation/diagnosis and consider the strongest competing explanations or diagnoses.

Respond with a JSON object containing exactly three keys:
- "warrant": string
- "backing": string
- "citations": array of objects, each with "source" (string), "url" (string), "year" (string or null), and "finding" (string — the specific recommendation or finding used)
