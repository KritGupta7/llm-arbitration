from fastapi import FastAPI
import asyncio

from app.models.arbitration_request import ArbitrationRequest
from app.arbitration import arbitrate

app = FastAPI()


@app.get("/")
def root():
    return {
        "message": "LLM Arbitration System"
    }


@app.post("/arbitrate")
async def arbitrate_answer(
    request: ArbitrationRequest
):
    verdict = await arbitrate(
        request.question,
        request.answer
    )

    return verdict