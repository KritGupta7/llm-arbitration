from pydantic import BaseModel


class Disagreement(BaseModel):
    type: str
    description: str
    severity: str  # "low", "medium", "high"
