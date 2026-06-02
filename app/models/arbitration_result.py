from pydantic import BaseModel
from app.models.critique import Critique, Issue
from app.models.disagreement import Disagreement


class ArbitrationResult(BaseModel):
    final_score: float
    confidence_level: str
    summary: str
    confirmed_issues: list[Issue]
    dismissed_issues: list[Issue] = []
    disagreements: list[Disagreement] = []
    warnings: list[str] = []
    accuracy: Critique
    logic: Critique
    completeness: Critique
