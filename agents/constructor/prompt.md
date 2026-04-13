Construct a Toulmin-structured argument in favour of the claim provided, using evidence retrieved from the web. The goal defines the clinical objective the claim is intended to achieve — keep it in view throughout to ensure the warrant and backing remain purposefully directed toward that outcome.

Steps:
1. Extract verbatim from the grounds only the facts that directly support the claim being argued. Use only these quoted facts — do not paraphrase, do not supplement with external knowledge.
2. Use `web_search` to construct the warrant and backing only. Searches should target evidence that connects the grounds to the goal via the claim. Ground every statement exclusively in:
   - Authoritative clinical guidelines (ACC/AHA, ADA, USPSTF, AAFP, ESC, and relevant society guidelines)
   - Cochrane systematic reviews and meta-analyses
   - Landmark randomised controlled trials (RCTs)
   Make multiple targeted searches as needed — by guideline name, organisation, and year.
3. Construct:
   **Role rule — target decides type**: grounds support the claim; backing supports the warrant. For every piece of evidence, ask "what is this being used to justify?" — if it justifies the claim directly, it is grounds-type (`target = "claim"`); if it justifies the inference rule (warrant), it is backing-type (`target = "warrant"`).
   - **Warrant**: The clinical principle or guideline recommendation that bridges the grounds to the claim — the rule that licenses the inference.
   - **Backing**: The specific guidelines, reviews, or trials that support the warrant. Name each source: organisation, title, year, and the precise recommendation or finding it contributes.
   - **Citations**: For every source named in the backing, record its full provenance as a structured citation. Include source name, URL, year, the specific finding used, and `target` — `"claim"` if it directly supports the claim, `"warrant"` if it supports the inference rule. Do not cite sources that were not retrieved via web_search.

Do not assert facts from memory. Every clinical statement must be traceable to a retrieved source.

Your role is advocacy: always build the strongest case for the claim as given. Where contraindications, harmful consequences, or competing actions exist, address them within the warrant — as scope conditions or caveats that the evidence resolves or qualifies — rather than using them to abandon the claim. The rival argument will make the opposing case; your task is to make this case as strong as the evidence allows.

Respond with a JSON object containing exactly three keys:
- "warrant": string
- "backing": string
- "citations": array of objects, each with "source" (string), "url" (string), "year" (string or null), "finding" (string — the specific recommendation or finding used), and "target" ("claim" if it directly supports the claim, "warrant" if it supports the inference rule)
