import logging
import os
import tomllib
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from langsmith import traceable
from log_config import short

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


@traceable
def run(claim: str) -> str:
    logger.debug("Inverter start | claim: %s", short(claim))
    llm = ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ["OPENROUTER_LIGHT_MODEL"],
        temperature=CONFIG["temperature"],
    )
    response = llm.invoke([
        SystemMessage(content=PROMPT),
        HumanMessage(content=claim),
    ])
    result = response.content.strip()
    logger.debug("Inverter done | %s → %s", short(claim), short(result))
    return result
