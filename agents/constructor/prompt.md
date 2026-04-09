Construct a Toulmin-structured argument in favour of the claim provided, using evidence retrieved from the web.

Steps:
1. Extract verbatim from the grounds only the facts that directly support the claim being argued. Use only these quoted facts — do not paraphrase, do not supplement with external knowledge.
2. Use `web_search` to construct the warrant and backing only. Ground every statement exclusively in:
   - Authoritative clinical guidelines (ACC/AHA, ADA, USPSTF, AAFP, ESC, and relevant society guidelines)
   - Cochrane systematic reviews and meta-analyses
   - Landmark randomised controlled trials (RCTs)
   Make multiple targeted searches as needed — by guideline name, organisation, and year.
3. Construct:
   - **Warrant**: The clinical principle or guideline recommendation that bridges the grounds to the claim — the rule that licenses the inference.
   - **Backing**: The specific guidelines, reviews, or trials that support the warrant. Name each source: organisation, title, year, and the precise recommendation or finding it contributes.

Do not assert facts from memory. Every clinical statement must be traceable to a retrieved source.

Respond with a JSON object containing exactly two keys:
- "warrant": string
- "backing": string
