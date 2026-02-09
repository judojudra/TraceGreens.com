from datetime import datetime
from decimal import Decimal

from sqlalchemy import Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.config import settings
from app.database import Base


class SeedInventory(Base):
    __tablename__ = "seed_inventory"

    id: Mapped[int] = mapped_column(primary_key=True)
    variety: Mapped[str] = mapped_column(String(100))
    variety_code: Mapped[str] = mapped_column(String(10), unique=True)
    supplier: Mapped[str] = mapped_column(String(200))
    lot_number: Mapped[str] = mapped_column(String(100))
    cost_per_kg: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    quantity_kg: Mapped[Decimal] = mapped_column(Numeric(10, 3), default=Decimal("0"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    @property
    def cost_per_tray(self) -> Decimal:
        """Cost per tray based on standard seed weight (25g = 0.025kg)."""
        return self.cost_per_kg * Decimal(str(settings.SEED_WEIGHT_G / 1000))
