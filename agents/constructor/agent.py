import json
import os
import tomllib
from pathlib import Path

from openai import OpenAI

import tools.web_search as web_search
from models import Argument, Citation

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(argument: Argument) -> Argument:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": f"Claim: {argument.claim}\n\nGoal: {argument.goal}\n\nGrounds: {argument.grounds}"},
    ]

    while True:
        response = client.chat.completions.create(
            model=os.environ["OPENROUTER_MODEL"],
            temperature=CONFIG["temperature"],
            messages=messages,
            tools=[web_search.SCHEMA],
            response_format={"type": "json_object"},
        )
        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            break

        for call in msg.tool_calls:
            result = web_search.execute(
                query=json.loads(call.function.arguments)["query"],
                **CONFIG["web_search"],
            )
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    result = json.loads(msg.content)
    citations = [Citation(**c) for c in result.get("citations", [])]
    return Argument(
        claim=argument.claim,
        goal=argument.goal,
        grounds=argument.grounds,
        warrant=result["warrant"],
        backing=result["backing"],
        citations=citations,
    )
