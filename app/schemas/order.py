from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class OrderCreate(BaseModel):
    customer_id: int
    batch_id: int
    quantity_g: Decimal = Field(..., gt=0)
    price_per_g: Decimal = Field(default=Decimal("1.6"), gt=0)


class OrderResponse(BaseModel):
    id: int
    customer_id: int
    batch_id: int
    quantity_g: Decimal
    price_per_g: Decimal
    total_price: Decimal
    order_date: date
    created_at: datetime

    model_config = {"from_attributes": True}
