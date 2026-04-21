import logging
import os
import tomllib
from pathlib import Path

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from langsmith import traceable
from log_config import short
from models import ArgumentPair
from schemas import ResolverOutput

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


@traceable
def run(pair: ArgumentPair) -> ResolverOutput:
    logger.debug("Resolver start | root claim: %s", short(pair.node.argument.claim))

    result: ResolverOutput = _chain().invoke([
        SystemMessage(content=PROMPT),
        HumanMessage(content=pair.model_dump_json()),
    ])

    logger.debug("Resolver done | verdict=%s  references=%d",
                 result.verdict, len(result.references))
    return result


def _chain():
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ["OPENROUTER_MODEL"],
        temperature=CONFIG["temperature"],
    ).with_structured_output(ResolverOutput)
