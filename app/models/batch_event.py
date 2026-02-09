from datetime import datetime
from typing import Optional

from sqlalchemy import ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class BatchEvent(Base):
    __tablename__ = "batch_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    event_type: Mapped[str] = mapped_column(String(20))  # "auto" or "manual"
    description: Mapped[str] = mapped_column(Text)
    photo_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    batch = relationship("Batch", back_populates="events")
