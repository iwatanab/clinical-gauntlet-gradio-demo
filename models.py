from typing import Optional
from pydantic import BaseModel


class Argument(BaseModel):
    claim: str
    goal: str
    patient_facts: str
    warrant: Optional[str] = None
    backing: Optional[str] = None


class ArgumentNode(BaseModel):
    argument: Argument
    allowed_to_spawn: bool = False
    candidate_claims: list[str] = []
    child_pairs: list["ArgumentPair"] = []
    depth: int = 0


class ArgumentPair(BaseModel):
    node: ArgumentNode
    rival_node: Optional[ArgumentNode] = None
    arbiter_reasoning: str = ""


ArgumentNode.model_rebuild()
ArgumentPair.model_rebuild()
