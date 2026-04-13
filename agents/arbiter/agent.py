import json
import os
import tomllib
from pathlib import Path
from typing import Optional

from openai import OpenAI

from models import ArgumentNode, ArbiterNodeInput

_dir = Path(__file__).parent
PROMPT = (_dir / "prompt.md").read_text()
CONFIG = tomllib.loads((_dir / "config.toml").read_text())


def run(node: ArgumentNode, rival_node: Optional[ArgumentNode]) -> dict:
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
