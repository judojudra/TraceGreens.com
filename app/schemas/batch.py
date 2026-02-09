from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class BatchCreate(BaseModel):
    seed_inventory_id: int
    sow_date: date = Field(default_factory=date.today)
    sowing_weight_g: Decimal = Field(default=Decimal("25.0"), ge=0)
    notes: Optional[str] = None


class BatchUpdate(BaseModel):
    sowing_weight_g: Optional[Decimal] = Field(None, ge=0)
    mold_incident: Optional[bool] = None
    notes: Optional[str] = None


class BatchTransition(BaseModel):
    new_status: str = Field(..., examples=["Light"])
    yield_weight_g: Optional[Decimal] = Field(None, ge=0)
    mold_incident: Optional[bool] = None
    notes: Optional[str] = None


class BatchResponse(BaseModel):
    id: int
    batch_id: str
    seed_inventory_id: int
    variety: str
    status: str
    sow_date: date
    blackout_end_date: date
    harvest_target_start: date
    harvest_target_end: date
    actual_harvest_date: Optional[date]
    sowing_weight_g: Decimal
    yield_weight_g: Optional[Decimal]
    mold_incident: bool
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
