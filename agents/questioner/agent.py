import json
import os
import tomllib
from pathlib import Path

from openai import OpenAI

from models import ArgumentNode

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(node: ArgumentNode) -> list[str]:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    response = client.chat.completions.create(
        model=os.environ["OPENROUTER_MODEL"],
        temperature=CONFIG["temperature"],
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": node.argument.model_dump_json()},
        ],
        response_format={"type": "json_object"},
    )
    result = json.loads(response.choices[0].message.content)
    return result["critical_questions"]
