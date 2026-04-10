import json
import os
import tomllib
from pathlib import Path
from typing import Optional

from openai import OpenAI

from models import ArgumentNode

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(node: ArgumentNode, rival_node: Optional[ArgumentNode]) -> dict:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    user_content = json.dumps({
        "node": node.model_dump(),
        "rival_node": rival_node.model_dump() if rival_node else None,
    })

    response = client.chat.completions.create(
        model=os.environ["OPENROUTER_MODEL"],
        temperature=CONFIG["temperature"],
        messages=[
            {"role": "system", "content": PROMPT},
            {"role": "user", "content": user_content},
        ],
        response_format={"type": "json_object"},
    )
    return json.loads(response.choices[0].message.content)
