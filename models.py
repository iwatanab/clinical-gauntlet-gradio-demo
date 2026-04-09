from typing import Optional
from pydantic import BaseModel


class Argument(BaseModel):
    claim: str
    grounds: str
    warrant: Optional[str] = None
    backing: Optional[str] = None
