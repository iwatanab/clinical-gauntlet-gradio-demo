import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from openai import OpenAI

from models import Argument, ArgumentNode, ArgumentPair
from agents.constructor import agent as constructor
from agents.arbiter import agent as arbiter
from agents.questioner import agent as questioner
from agents.resolver import agent as resolver

MAX_DEPTH = int(os.environ.get("MAX_DEPTH", 2))


def _rival_claim(claim: str) -> str:
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    response = client.chat.completions.create(
        model=os.environ["OPENROUTER_LIGHT_MODEL"],
        messages=[
            {"role": "system", "content": (
                "Negate the claim by toggling its polarity — positive to negative, negative to positive. Change nothing else. "
                "e.g. 'should be initiated' → 'should not be initiated'; 'should not be withheld' → 'should be withheld'. "
                "Return only the result. No explanation"
            )},
            {"role": "user", "content": claim},
        ],
    )
    return response.choices[0].message.content.strip()


def _build_pair(arg: Argument, rival_arg: Optional[Argument], depth: int) -> ArgumentPair:
    # Step 1: Constructor (parallel if rival present)
    with ThreadPoolExecutor(max_workers=2) as pool:
        node_future = pool.submit(constructor.run, arg)
        rival_future = pool.submit(constructor.run, rival_arg) if rival_arg else None

    node = ArgumentNode(argument=node_future.result(), depth=depth)
    rival_node = ArgumentNode(argument=rival_future.result(), depth=depth) if rival_future else None

    # Step 2: Questioner (parallel, both nodes — runs before Arbiter so Arbiter is informed)
    all_nodes = [n for n in [node, rival_node] if n]
    with ThreadPoolExecutor(max_workers=len(all_nodes)) as pool:
        q_futures = [pool.submit(questioner.run, n) for n in all_nodes]
    for n, fut in zip(all_nodes, q_futures):
        n.critical_questions = fut.result()

    # Step 3: Arbiter (cross-sibling gate + claim synthesis, up to 2 per allowed node)
    arbiter_result = arbiter.run(node, rival_node)
    node.allowed_to_spawn = arbiter_result["node_allowed"] and depth < MAX_DEPTH
    if rival_node:
        rival_node.allowed_to_spawn = arbiter_result["rival_allowed"] and depth < MAX_DEPTH

    # Step 4: Recurse directly from Arbiter's claim lists
    for n, claims_key in [(node, "node_claims"), (rival_node, "rival_claims")]:
        if n is None:
            continue
        claims = arbiter_result.get(claims_key, [])
        n.spawned_claims = [c["claim"] for c in claims]  # always record — Resolver uses this to detect depth-capped nodes
        if not n.allowed_to_spawn:
            continue
        for c in claims:
            child_arg = Argument(claim=c["claim"], goal=arg.goal, grounds=arg.grounds)
            child_rival_arg = None
            if c["has_rival"]:
                child_rival_arg = Argument(
                    claim=_rival_claim(c["claim"]),
                    goal=arg.goal,
                    grounds=arg.grounds,
                )
            n.child_pairs.append(_build_pair(child_arg, child_rival_arg, depth + 1))

    return ArgumentPair(
        node=node,
        rival_node=rival_node,
        arbiter_reasoning=arbiter_result["reasoning"],
    )


def run_pipeline(argument: Argument) -> dict:
    rival_arg = Argument(
        claim=_rival_claim(argument.claim),
        goal=argument.goal,
        grounds=argument.grounds,
    )
    root_pair = _build_pair(argument, rival_arg, depth=0)
    resolution = resolver.run(root_pair)
    return {
        "tree": root_pair.model_dump(),
        "verdict": resolution["verdict"],
        "justification": resolution["justification"],
        "recommendation": resolution["recommendation"],
        "references": resolution["references"],
    }
