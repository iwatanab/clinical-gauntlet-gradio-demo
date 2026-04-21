import logging
import os
import tomllib
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from log_config import short
from models import Argument
from schemas import QuestionerOutput

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(argument: Argument) -> list[str]:
    logger.debug("Questioner start | claim: %s", short(argument.claim))

    result = _chain().invoke([
        SystemMessage(content=PROMPT),
        HumanMessage(content=argument.model_dump_json()),
    ])

    logger.debug("Questioner done | %d questions for: %s",
                 len(result.critical_questions), short(argument.claim))
    return result.critical_questions


def _chain():
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ["OPENROUTER_MODEL"],
        temperature=CONFIG["temperature"],
    ).with_structured_output(QuestionerOutput)
