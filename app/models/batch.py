from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import Date, ForeignKey, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

VALID_STATUSES = ("Blackout", "Light", "Harvested", "Discarded")

TRANSITIONS = {
    "Blackout": ["Light"],
    "Light": ["Harvested", "Discarded"],
    "Harvested": [],
    "Discarded": [],
}


class Batch(Base):
    __tablename__ = "batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    seed_inventory_id: Mapped[int] = mapped_column(ForeignKey("seed_inventory.id"))
    status: Mapped[str] = mapped_column(String(20), default="Blackout")
    sow_date: Mapped[date] = mapped_column(Date)
    blackout_end_date: Mapped[date] = mapped_column(Date)
    harvest_target_start: Mapped[date] = mapped_column(Date)
    harvest_target_end: Mapped[date] = mapped_column(Date)
    actual_harvest_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    sowing_weight_g: Mapped[Decimal] = mapped_column(Numeric(8, 2), default=Decimal("25.0"))
    yield_weight_g: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2), nullable=True)
    mold_incident: Mapped[bool] = mapped_column(default=False)
    notes: Mapped[Optional[str]] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    seed_inventory = relationship("SeedInventory", lazy="joined")
    events = relationship("BatchEvent", back_populates="batch", order_by="BatchEvent.created_at", lazy="select")
