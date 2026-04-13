from typing import Literal, Optional
from pydantic import BaseModel

# Toulmin structure:
#   grounds  → support the CLAIM         (Citation.target = "claim")
#   warrant  → bridges grounds to claim  (the inference rule itself)
#   backing  → supports the WARRANT      (Citation.target = "warrant")
#
# Decision rule — target decides type:
#   ask "what is this item being used to justify?"
#   → the claim itself    = grounds  (target = "claim")
#   → the inference rule  = backing  (target = "warrant")


class Citation(BaseModel):
    source: str   # e.g. "ACC/AHA Atrial Fibrillation Guidelines 2023"
    url: str
    year: Optional[str] = None
    finding: str  # specific recommendation or finding used
    target: Literal["claim", "warrant"] = "warrant"
    # "claim"   → directly supports the claim (grounds-type evidence)
    # "warrant" → justifies the inference rule (backing-type evidence)


class Argument(BaseModel):
    claim: str
    goal: str
    grounds: str
    warrant: Optional[str] = None
    backing: Optional[str] = None
    citations: list[Citation] = []


class ArgumentNode(BaseModel):
    argument: Argument
    allowed_to_spawn: bool = False
    critical_questions: list[str] = []  # from Questioner
    spawned_claims: list[str] = []      # from Arbiter (up to 2)
    child_pairs: list["ArgumentPair"] = []
    depth: int = 0


class ArgumentPair(BaseModel):
    node: ArgumentNode
    rival_node: Optional[ArgumentNode] = None
    arbiter_reasoning: str = ""


ArgumentNode.model_rebuild()
ArgumentPair.model_rebuild()


class ArbiterNodeInput(BaseModel):
    """Lean projection of ArgumentNode for Arbiter input — no pipeline metadata."""
    argument: Argument
    critical_questions: list[str] = []
