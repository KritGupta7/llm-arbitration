from pydantic import BaseModel


class ArbitrationRequest(BaseModel):
    question: str
    answer: str