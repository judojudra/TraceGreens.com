from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class SeedInventoryCreate(BaseModel):
    variety: str = Field(..., max_length=100, examples=["Radish"])
    variety_code: str = Field(..., max_length=10, examples=["RAD"])
    supplier: str = Field(..., max_length=200, examples=["Mumbai Seeds Co."])
    lot_number: str = Field(..., max_length=100, examples=["RAD-2026-001"])
    cost_per_kg: Decimal = Field(..., gt=0, examples=[800.00])
    quantity_kg: Decimal = Field(default=Decimal("0"), ge=0, examples=[5.0])


class SeedInventoryUpdate(BaseModel):
    variety: Optional[str] = Field(None, max_length=100)
    supplier: Optional[str] = Field(None, max_length=200)
    lot_number: Optional[str] = Field(None, max_length=100)
    cost_per_kg: Optional[Decimal] = Field(None, gt=0)
    quantity_kg: Optional[Decimal] = Field(None, ge=0)


class SeedInventoryResponse(BaseModel):
    id: int
    variety: str
    variety_code: str
    supplier: str
    lot_number: str
    cost_per_kg: Decimal
    quantity_kg: Decimal
    cost_per_tray: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
