from pydantic import BaseModel
from app.models.critique import Critique, Issue


class ArbitrationResult(BaseModel):
    final_score: float
    confidence_level: str
    summary: str
    confirmed_issues: list[Issue]
    accuracy: Critique
    logic: Critique
    completeness: Critique
