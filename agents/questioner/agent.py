import json
import logging
import os
import tomllib
from pathlib import Path

from openai import OpenAI

from log_config import short, parse_json
from models import Argument

logger = logging.getLogger(__name__)

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(argument: Argument) -> list[str]:
    logger.debug("Questioner start | claim: %s", short(argument.claim))
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
                {"role": "user", "content": argument.model_dump_json()},
            ],
            response_format={"type": "json_object"},
        )
    except Exception:
        logger.exception("Questioner — API call failed (claim: %s)", short(argument.claim))
        raise

    try:
        result = parse_json(response.choices[0].message.content)
    except Exception:
        logger.exception("Questioner — JSON parse failed | raw: %s",
                         short(str(response.choices[0].message.content), 200))
        raise

    questions = result["critical_questions"]
    logger.debug("Questioner done | %d questions for: %s", len(questions), short(argument.claim))
    return questions
