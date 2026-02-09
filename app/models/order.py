from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Numeric, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"))
    batch_id: Mapped[int] = mapped_column(ForeignKey("batches.id"))
    quantity_g: Mapped[Decimal] = mapped_column(Numeric(8, 2))
    price_per_g: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("1.6"))
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    order_date: Mapped[date] = mapped_column(Date, server_default=func.current_date())
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    customer = relationship("Customer", lazy="joined")
    batch = relationship("Batch", lazy="joined")
