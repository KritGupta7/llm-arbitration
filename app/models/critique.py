from pydantic import BaseModel


class Critique(BaseModel):
    score: int
    issue: str
    explanation: str