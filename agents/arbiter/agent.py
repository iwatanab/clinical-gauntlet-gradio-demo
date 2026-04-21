import json
import logging
import os
import tomllib
from pathlib import Path
from typing import Optional

from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage

from log_config import short
from models import ArgumentNode, ArbiterNodeInput
from schemas import ArbiterOutput

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(node: ArgumentNode, rival_node: Optional[ArgumentNode]) -> ArbiterOutput:
    logger.debug("Arbiter start | node: %s | rival: %s",
                 short(node.argument.claim),
                 short(rival_node.argument.claim) if rival_node else "(none)")

    node_input = ArbiterNodeInput(argument=node.argument, critical_questions=node.critical_questions)
    rival_input = ArbiterNodeInput(argument=rival_node.argument, critical_questions=rival_node.critical_questions) if rival_node else None

    user_content = json.dumps({
        "node": node_input.model_dump(),
        "rival_node": rival_input.model_dump() if rival_input else None,
    })

    result: ArbiterOutput = _chain().invoke([
        SystemMessage(content=PROMPT),
        HumanMessage(content=user_content),
    ])

    logger.debug("Arbiter done | node_allowed=%s  rival_allowed=%s  node_claims=%d  rival_claims=%d",
                 result.node_allowed, result.rival_allowed,
                 len(result.node_claims), len(result.rival_claims))
    return result


def _chain():
    return ChatOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
        model=os.environ["OPENROUTER_MODEL"],
        temperature=CONFIG["temperature"],
    ).with_structured_output(ArbiterOutput)
