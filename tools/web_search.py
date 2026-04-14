import os
from tavily import TavilyClient

SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for authoritative evidence on a topic.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
            },
            "required": ["query"],
        },
    },
}


def execute(query: str, search_depth: str = "advanced", max_results: int = 3) -> str:
    results = TavilyClient(api_key=os.environ["TAVILY_API_KEY"]).search(
        query=query, search_depth=search_depth, max_results=max_results
    )
    return "\n\n".join(
        f"[{r['url']}]\n{r['content']}" for r in results.get("results", [])
    )
