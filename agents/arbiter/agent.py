import json
import logging
import os
import tomllib
from pathlib import Path
from typing import Optional

from openai import OpenAI

from log_config import short
from models import ArgumentNode, ArbiterNodeInput

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(node: ArgumentNode, rival_node: Optional[ArgumentNode]) -> dict:
    logger.debug("Arbiter start | node: %s | rival: %s",
                 short(node.argument.claim),
                 short(rival_node.argument.claim) if rival_node else "(none)")

    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    node_input = ArbiterNodeInput(argument=node.argument, critical_questions=node.critical_questions)
    rival_input = ArbiterNodeInput(argument=rival_node.argument, critical_questions=rival_node.critical_questions) if rival_node else None

    user_content = json.dumps({
        "node": node_input.model_dump(),
        "rival_node": rival_input.model_dump() if rival_input else None,
    })

    try:
        response = client.chat.completions.create(
            model=os.environ["OPENROUTER_MODEL"],
            temperature=CONFIG["temperature"],
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": user_content},
            ],
            response_format={"type": "json_object"},
        )
    except Exception:
        logger.exception("Arbiter — API call failed (node claim: %s)", short(node.argument.claim))
        raise

    try:
        result = json.loads(response.choices[0].message.content)
    except Exception:
        logger.exception("Arbiter — JSON parse failed | raw: %s",
                         short(str(response.choices[0].message.content), 200))
        raise

    required = {"node_allowed", "rival_allowed", "reasoning", "node_claims", "rival_claims"}
    missing = required - result.keys()
    if missing:
        logger.error("Arbiter — response missing keys: %s | raw: %s", missing,
                     short(str(result), 300))
        raise ValueError(f"Arbiter response missing required keys: {missing}")

    logger.debug("Arbiter done | node_allowed=%s  rival_allowed=%s  node_claims=%d  rival_claims=%d",
                 result.get("node_allowed"), result.get("rival_allowed"),
                 len(result.get("node_claims", [])), len(result.get("rival_claims", [])))
    return result
