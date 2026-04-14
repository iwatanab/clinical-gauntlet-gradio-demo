import logging
import os
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

from openai import OpenAI

from log_config import short
from models import Argument, ArgumentNode, ArgumentPair
from agents.constructor import agent as constructor
from agents.arbiter import agent as arbiter
from agents.questioner import agent as questioner
from agents.resolver import agent as resolver

logger = logging.getLogger(__name__)

MAX_DEPTH = int(os.environ.get("MAX_DEPTH", 2))


def _spawn_pair(claim: str, has_rival: bool, goal: str, grounds: str, depth: int,
                *, path: str, on_event=None) -> ArgumentPair:
    """Build a child ArgumentPair, generating the rival claim inside the thread if needed."""
    child_arg = Argument(claim=claim, goal=goal, grounds=grounds)
    child_rival_arg = None
    if has_rival:
        logger.debug("_spawn_pair | generating rival for: %s", short(claim))
        child_rival_arg = Argument(claim=_rival_claim(claim), goal=goal, grounds=grounds)
    return _build_pair(child_arg, child_rival_arg, depth, path=path, on_event=on_event)


def _rival_claim(claim: str) -> str:
    logger.debug("rival_claim | input: %s", short(claim))
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
    result = response.choices[0].message.content.strip()
    logger.debug("rival_claim | output: %s", short(result))
    return result


def _build_pair(arg: Argument, rival_arg: Optional[Argument], depth: int,
                *, path: str = "root", on_event=None) -> ArgumentPair:
    tag = f"[depth={depth}]"
    logger.info("%s ── Building pair", tag)
    logger.info("%s    node : %s", tag, short(arg.claim))
    logger.info("%s    rival: %s", tag, short(rival_arg.claim) if rival_arg else "(none)")

    if on_event:
        on_event({"type": "pair_started", "path": path, "depth": depth, "data": {
            "claim": arg.claim,
            "rival_claim": rival_arg.claim if rival_arg else None,
            "goal": arg.goal,
            "grounds": arg.grounds,
        }})

    # Step 1: Constructor — parallel when rival present
    logger.info("%s Step 1 — Constructor × %d", tag, 2 if rival_arg else 1)
    try:
        args_to_construct = [a for a in [arg, rival_arg] if a is not None]
        with ThreadPoolExecutor(max_workers=len(args_to_construct)) as pool:
            built = list(pool.map(constructor.run, args_to_construct))
        node = ArgumentNode(argument=built[0], depth=depth)
        rival_node = ArgumentNode(argument=built[1], depth=depth) if rival_arg else None
    except Exception:
        logger.exception("%s Constructor failed (node claim: %s)", tag, short(arg.claim))
        raise

    logger.info("%s Constructor done | node citations=%d%s", tag,
                len(node.argument.citations),
                f"  rival citations={len(rival_node.argument.citations)}" if rival_node else "")

    if on_event:
        on_event({"type": "constructor_done", "path": path, "depth": depth, "data": {
            "node_argument": node.argument.model_dump(),
            "rival_argument": rival_node.argument.model_dump() if rival_node else None,
        }})

    # Step 2: Questioner — parallel for both nodes
    logger.info("%s Step 2 — Questioner × %d", tag, 2 if rival_node else 1)
    all_nodes = [n for n in [node, rival_node] if n]
    try:
        with ThreadPoolExecutor(max_workers=len(all_nodes)) as pool:
            questions_list = list(pool.map(questioner.run, [n.argument for n in all_nodes]))
        for n, questions in zip(all_nodes, questions_list):
            n.critical_questions = questions
    except Exception:
        logger.exception("%s Questioner failed", tag)
        raise

    logger.info("%s Questioner done | node questions=%d%s", tag,
                len(node.critical_questions),
                f"  rival questions={len(rival_node.critical_questions)}" if rival_node else "")
    for q in node.critical_questions:
        logger.debug("%s   [node Q] %s", tag, short(q))
    if rival_node:
        for q in rival_node.critical_questions:
            logger.debug("%s   [rival Q] %s", tag, short(q))

    if on_event:
        on_event({"type": "questioner_done", "path": path, "depth": depth, "data": {
            "node_questions": node.critical_questions,
            "rival_questions": rival_node.critical_questions if rival_node else None,
        }})

    # Step 3: Arbiter — cross-sibling gate + claim synthesis
    logger.info("%s Step 3 — Arbiter", tag)
    try:
        arbiter_result = arbiter.run(node, rival_node)
    except Exception:
        logger.exception("%s Arbiter failed", tag)
        raise

    node.allowed_to_spawn = arbiter_result["node_allowed"] and depth < MAX_DEPTH
    if rival_node:
        rival_node.allowed_to_spawn = arbiter_result["rival_allowed"] and depth < MAX_DEPTH

    logger.info("%s Arbiter done | node_allowed=%s (will_spawn=%s)  rival_allowed=%s (will_spawn=%s)",
                tag,
                arbiter_result["node_allowed"], node.allowed_to_spawn,
                arbiter_result.get("rival_allowed"), rival_node.allowed_to_spawn if rival_node else "n/a")
    logger.debug("%s Arbiter reasoning: %s", tag, short(arbiter_result.get("reasoning", ""), 200))

    for label, claims_key in [("node", "node_claims"), ("rival", "rival_claims")]:
        for c in arbiter_result.get(claims_key, []):
            logger.debug("%s   [%s claim] has_rival=%s | %s", tag, label, c["has_rival"], short(c["claim"]))

    if on_event:
        on_event({"type": "arbiter_done", "path": path, "depth": depth, "data": {
            "node_allowed": node.allowed_to_spawn,
            "rival_allowed": rival_node.allowed_to_spawn if rival_node else None,
            "arbiter_reasoning": arbiter_result["reasoning"],
            "node_spawned_claims": [c["claim"] for c in arbiter_result.get("node_claims", [])],
            "rival_spawned_claims": [c["claim"] for c in arbiter_result.get("rival_claims", [])],
        }})

    # Step 4: Collect all pending child spawns across both node and rival, then build in parallel.
    # spawned_claims is always set (even when not spawning) so the Resolver can detect depth-capped nodes.
    # _rival_claim generation happens inside each thread via _spawn_pair — fully concurrent.
    pending = []  # (parent_node, claim_text, has_rival, child_path)
    for n, claims_key, allowed_key, label, child_prefix in [
        (node,       "node_claims",  "node_allowed",  "node",  "n"),
        (rival_node, "rival_claims", "rival_allowed", "rival", "r"),
    ]:
        if n is None:
            continue
        claims = arbiter_result.get(claims_key, [])
        n.spawned_claims = [c["claim"] for c in claims]

        if not n.allowed_to_spawn:
            reason = "depth cap" if arbiter_result.get(allowed_key) else "arbiter stopped"
            logger.info("%s [%s] Not spawning (%s) — %d claim(s) recorded", tag, label, reason, len(claims))
            continue

        logger.info("%s [%s] Queuing %d child pair(s)", tag, label, len(claims))
        for i, c in enumerate(claims):
            child_path = f"{path}.{child_prefix}{i}"
            pending.append((n, c["claim"], c["has_rival"], child_path))

    if pending:
        logger.info("%s Step 4 — Building %d child pair(s) in parallel", tag, len(pending))
        try:
            with ThreadPoolExecutor(max_workers=len(pending)) as pool:
                futures = [
                    pool.submit(_spawn_pair, claim, has_rival, arg.goal, arg.grounds, depth + 1,
                                path=child_path, on_event=on_event)
                    for _, claim, has_rival, child_path in pending
                ]
            for (parent_n, _, _, _), fut in zip(pending, futures):
                parent_n.child_pairs.append(fut.result())
        except Exception:
            logger.exception("%s Child pair construction failed", tag)
            raise

    if on_event:
        on_event({"type": "pair_complete", "path": path, "depth": depth, "data": None})

    return ArgumentPair(
        node=node,
        rival_node=rival_node,
        arbiter_reasoning=arbiter_result["reasoning"],
    )


def run_pipeline(argument: Argument, *, on_event=None) -> dict:
    logger.info("══════════════════════════════════════════")
    logger.info("Pipeline start | MAX_DEPTH=%d", MAX_DEPTH)
    logger.info("Claim : %s", short(argument.claim))
    logger.info("Goal  : %s", short(argument.goal))
    logger.info("══════════════════════════════════════════")

    try:
        logger.info("Generating root rival claim")
        rival_arg = Argument(
            claim=_rival_claim(argument.claim),
            goal=argument.goal,
            grounds=argument.grounds,
        )
        logger.info("Root rival: %s", short(rival_arg.claim))
        root_pair = _build_pair(argument, rival_arg, depth=0, path="root", on_event=on_event)
    except Exception:
        logger.exception("Pipeline failed during tree construction")
        raise

    logger.info("Tree complete — running Resolver")
    try:
        resolution = resolver.run(root_pair)
    except Exception:
        logger.exception("Resolver failed")
        raise

    logger.info("══════════════════════════════════════════")
    logger.info("Pipeline complete | verdict: %s", resolution["verdict"])
    logger.info("══════════════════════════════════════════")

    if on_event:
        on_event({"type": "pipeline_complete", "path": "root", "depth": 0, "data": {
            "verdict": resolution["verdict"],
            "justification": resolution["justification"],
            "recommendation": resolution["recommendation"],
            "references": resolution["references"],
        }})

    return {
        "tree": root_pair.model_dump(),
        "verdict": resolution["verdict"],
        "justification": resolution["justification"],
        "recommendation": resolution["recommendation"],
        "references": resolution["references"],
    }
