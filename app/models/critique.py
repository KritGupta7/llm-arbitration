from pydantic import BaseModel, Field


class Issue(BaseModel):
    quote: str
    problem: str
    severity: int = Field(ge=1, le=5)


class Critique(BaseModel):
    dimension: str
    score: int = Field(ge=1, le=5)
    confidence: float = Field(ge=0.0, le=1.0)
    issues: list[Issue]
    explanation: str
