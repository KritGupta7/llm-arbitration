from pydantic import BaseModel
from app.models.critique import Critique


class ArbitrationResult(BaseModel):
    final_score: float
    accuracy: Critique
    logic: Critique
    completeness: Critique