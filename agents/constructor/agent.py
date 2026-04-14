import json
import logging
import os
import tomllib
from pathlib import Path

from openai import OpenAI

import tools.web_search as web_search
from log_config import short, parse_json
from models import Argument, Citation

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(argument: Argument) -> Argument:
    logger.debug("Constructor start | claim: %s", short(argument.claim))
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    messages = [
        {"role": "system", "content": PROMPT},
        {"role": "user", "content": f"Claim: {argument.claim}\n\nGoal: {argument.goal}\n\nGrounds: {argument.grounds}"},
    ]

    search_count = 0
    while True:
        try:
            response = client.chat.completions.create(
                model=os.environ["OPENROUTER_MODEL"],
                temperature=CONFIG["temperature"],
                messages=messages,
                tools=[web_search.SCHEMA],
                response_format={"type": "json_object"},
            )
        except Exception:
            logger.exception("Constructor — API call failed (claim: %s)", short(argument.claim))
            raise

        msg = response.choices[0].message
        messages.append(msg)

        if not msg.tool_calls:
            break

        for call in msg.tool_calls:
            query = json.loads(call.function.arguments)["query"]
            search_count += 1
            logger.debug("Constructor search #%d | query: %s", search_count, short(query))
            try:
                result = web_search.execute(query=query, **CONFIG["web_search"])
            except Exception:
                logger.exception("Constructor — web_search failed (query: %s)", short(query))
                raise
            messages.append({"role": "tool", "tool_call_id": call.id, "content": result})

    try:
        result = parse_json(msg.content)
    except Exception:
        logger.exception("Constructor — JSON parse failed | raw: %s", short(str(msg.content), 200))
        raise

    citations = [Citation(**c) for c in result.get("citations", [])]
    logger.debug("Constructor done | searches=%d  citations=%d | claim: %s",
                 search_count, len(citations), short(argument.claim))
    return Argument(
        claim=argument.claim,
        goal=argument.goal,
        grounds=argument.grounds,
        warrant=result["warrant"],
        backing=result["backing"],
        citations=citations,
    )
