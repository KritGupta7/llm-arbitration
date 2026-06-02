from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.database import engine
from app.models.db_models import Base
from app.models.arbitration_request import ArbitrationRequest
from app.models.arbitration_result import ArbitrationResult
from app.arbitration import arbitrate
from app.repositories.arbitration_repository import (
    save_arbitration,
    get_arbitration,
    list_arbitrations,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(lifespan=lifespan)


class ArbitrationAPIResponse(BaseModel):
    id: int
    result: ArbitrationResult


class ArbitrationListItem(BaseModel):
    id: int
    question: str
    answer: str
    final_score: float
    confidence_level: str
    created_at: datetime


class ArbitrationDetailResponse(BaseModel):
    id: int
    question: str
    answer: str
    result: ArbitrationResult
    created_at: datetime


@app.get("/")
def root():
    return {"message": "LLM Arbitration System"}


@app.post("/arbitrate", response_model=ArbitrationAPIResponse)
async def arbitrate_answer(request: ArbitrationRequest):
    verdict = await arbitrate(request.question, request.answer)
    record = save_arbitration(request.question, request.answer, verdict)
    return ArbitrationAPIResponse(id=record.id, result=verdict)


@app.get("/arbitrations", response_model=list[ArbitrationListItem])
def get_arbitrations(limit: int = 20):
    records = list_arbitrations(limit=limit)
    return [
        ArbitrationListItem(
            id=r.id,
            question=r.question,
            answer=r.answer,
            final_score=r.final_score,
            confidence_level=r.confidence_level,
            created_at=r.created_at,
        )
        for r in records
    ]


@app.get("/arbitrations/{record_id}", response_model=ArbitrationDetailResponse)
def get_arbitration_by_id(record_id: int):
    record = get_arbitration(record_id)
    if record is None:
        raise HTTPException(
            status_code=404,
            detail=f"Arbitration {record_id} not found.",
        )
    result = ArbitrationResult.model_validate_json(record.result_json)
    return ArbitrationDetailResponse(
        id=record.id,
        question=record.question,
        answer=record.answer,
        result=result,
        created_at=record.created_at,
    )
