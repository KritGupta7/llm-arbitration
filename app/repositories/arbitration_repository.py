from app.database import SessionLocal
from app.models.db_models import ArbitrationRecord
from app.models.arbitration_result import ArbitrationResult


def save_arbitration(
    question: str,
    answer: str,
    result: ArbitrationResult,
) -> ArbitrationRecord:
    db = SessionLocal()
    try:
        record = ArbitrationRecord(
            question=question,
            answer=answer,
            result_json=result.model_dump_json(),
            final_score=result.final_score,
            confidence_level=result.confidence_level,
        )
        db.add(record)
        db.commit()
        db.refresh(record)
        return record
    finally:
        db.close()


def get_arbitration(record_id: int) -> ArbitrationRecord | None:
    db = SessionLocal()
    try:
        return db.get(ArbitrationRecord, record_id)
    finally:
        db.close()


def list_arbitrations(limit: int = 20) -> list[ArbitrationRecord]:
    db = SessionLocal()
    try:
        return (
            db.query(ArbitrationRecord)
            .order_by(ArbitrationRecord.created_at.desc())
            .limit(limit)
            .all()
        )
    finally:
        db.close()
