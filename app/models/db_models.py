from datetime import datetime, timezone

from sqlalchemy import Column, Integer, String, Float, Text, DateTime

from app.database import Base


class ArbitrationRecord(Base):
    __tablename__ = "arbitrations"

    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)
    answer = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    final_score = Column(Float, nullable=False)
    confidence_level = Column(String(16), nullable=False)
    created_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
