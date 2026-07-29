from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Integer, String, Text

from app.db.database import Base


class Receipt(Base):
    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, index=True)
    original_filename = Column(String, nullable=False)
    content_type = Column(String, nullable=False)
    saved_path = Column(String, nullable=False)
    extracted_text = Column(Text, nullable=True)
    document_type = Column(String, nullable=True)
    structured_data = Column(JSON, nullable=True)
    validation_result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
