import json
import logging
import os
import tomllib
from pathlib import Path

from openai import OpenAI

from log_config import short
from models import ArgumentPair

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(pair: ArgumentPair) -> dict:
    logger.debug("Resolver start | root claim: %s", short(pair.node.argument.claim))
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    try:
        response = client.chat.completions.create(
            model=os.environ["OPENROUTER_MODEL"],
            temperature=CONFIG["temperature"],
            messages=[
                {"role": "system", "content": PROMPT},
                {"role": "user", "content": pair.model_dump_json()},
            ],
            response_format={"type": "json_object"},
        )
    except Exception:
        logger.exception("Resolver — API call failed")
        raise

    try:
        result = json.loads(response.choices[0].message.content)
    except Exception:
        logger.exception("Resolver — JSON parse failed | raw: %s",
                         short(str(response.choices[0].message.content), 200))
        raise

    required = {"verdict", "justification", "recommendation", "references"}
    missing = required - result.keys()
    if missing:
        logger.error("Resolver — response missing keys: %s | raw: %s", missing,
                     short(str(result), 300))
        raise ValueError(f"Resolver response missing required keys: {missing}")

    valid_verdicts = {"survives", "defeated", "impasse"}
    verdict = result.get("verdict", "")
    if verdict not in valid_verdicts:
        logger.error("Resolver — unexpected verdict value: %r (expected one of %s)", verdict, valid_verdicts)

    logger.debug("Resolver done | verdict=%s  references=%d",
                 verdict, len(result.get("references", [])))
    return {
        "verdict": verdict,
        "justification": result["justification"],
        "recommendation": result["recommendation"],
        "references": result.get("references", []),
    }
