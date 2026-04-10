from typing import Optional
from pydantic import BaseModel


class Argument(BaseModel):
    claim: str
    goal: str
    patient_facts: str
    warrant: Optional[str] = None
    backing: Optional[str] = None
