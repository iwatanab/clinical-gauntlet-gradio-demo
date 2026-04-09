import os
from concurrent.futures import ThreadPoolExecutor
from openai import OpenAI
from models import Argument
from agents.constructor import agent as constructor


def _contraclaim(claim: str) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    response = client.chat.completions.create(
        model=os.environ["OPENROUTER_LIGHT_MODEL"],
        messages=[
            {"role": "system", "content": (
                "Produce a one-sentence clinical recommendation that opposes the claim by negating its conclusion only, "
                "leaving all stated patient facts, clinical context, and temporal framing unchanged. "
                "No explanation."
            )},
            {"role": "user", "content": claim},
        ],
    )
    return response.choices[0].message.content.strip()


def run_pipeline(argument: Argument) -> dict:
    contra_claim = _contraclaim(argument.claim)
    contra_argument = Argument(claim=contra_claim, grounds=argument.grounds)

    with ThreadPoolExecutor(max_workers=2) as pool:
        claim_future = pool.submit(constructor.run, argument)
        contra_future = pool.submit(constructor.run, contra_argument)

    return {
        "claim": claim_future.result().model_dump(),
        "contraclaim": contra_future.result().model_dump(),
    }
