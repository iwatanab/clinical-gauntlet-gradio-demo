import logging
import os
import tomllib
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage
from langchain_core.tools import tool as lc_tool

import tools.web_search as web_search
from langsmith import traceable
from log_config import short, parse_json
from models import Argument
from schemas import ConstructorOutput

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


@lc_tool
def search_web(query: str) -> str:
    """Search the web for authoritative clinical evidence."""
    return web_search.execute(query=query, **CONFIG["web_search"])


@traceable
def run(argument: Argument) -> Argument:
    logger.debug("Constructor start | claim: %s", short(argument.claim))

    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ["OPENROUTER_MODEL"],
        temperature=CONFIG["temperature"],
        model_kwargs={"response_format": {"type": "json_object"}},
    ).bind_tools([search_web])

    messages = [
        SystemMessage(content=PROMPT),
        HumanMessage(content=f"Claim: {argument.claim}\n\nGoal: {argument.goal}\n\nGrounds: {argument.grounds}"),
    ]

    search_count = 0
    while True:
        response = llm.invoke(messages)
        messages.append(response)
        if not response.tool_calls:
            break
        for tc in response.tool_calls:
            search_count += 1
            logger.debug("Constructor search #%d | query: %s", search_count, short(tc["args"]["query"]))
            result = search_web.invoke(tc["args"])
            messages.append(ToolMessage(content=str(result), tool_call_id=tc["id"]))

    # Validate final response against typed schema
    parsed = ConstructorOutput.model_validate(parse_json(response.content))

    logger.debug("Constructor done | searches=%d  citations=%d | claim: %s",
                 search_count, len(parsed.citations), short(argument.claim))
    return Argument(
        claim=argument.claim,
        goal=argument.goal,
        grounds=argument.grounds,
        warrant=parsed.warrant,
        backing=parsed.backing,
        citations=parsed.citations,
    )
