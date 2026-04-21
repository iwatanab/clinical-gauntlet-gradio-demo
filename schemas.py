"""Typed output schemas for each pipeline agent.

These replace raw dict parsing + manual key validation. The function-calling
protocol in with_structured_output is more reliable than json_object mode
across OpenRouter models, and Pydantic catches schema mismatches with
descriptive errors instead of opaque KeyError / JSONDecodeError.
"""

from typing import Literal

from pydantic import BaseModel

from models import Citation


class ConstructorOutput(BaseModel):
    warrant: str
    backing: str
    citations: list[Citation]


class QuestionerOutput(BaseModel):
    critical_questions: list[str]


class SpawnedClaim(BaseModel):
    claim: str
    has_rival: bool


class ArbiterOutput(BaseModel):
    node_allowed: bool
    rival_allowed: bool
    reasoning: str
    node_claims: list[SpawnedClaim]
    rival_claims: list[SpawnedClaim]


class ResolverOutput(BaseModel):
    verdict: Literal["survives", "defeated", "impasse"]
    justification: str
    recommendation: str
    references: list[dict]
