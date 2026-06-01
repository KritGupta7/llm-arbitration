from pydantic import BaseModel


class Issue(BaseModel):
    quote: str
    problem: str
    severity: int


class Critique(BaseModel):
    dimension: str
    score: int
    confidence: float
    issues: list[Issue]
    explanation: str
