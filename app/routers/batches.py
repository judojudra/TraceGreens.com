from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.batch import Batch
from app.schemas.batch import BatchCreate, BatchResponse, BatchTransition, BatchUpdate
from app.services.batch_service import create_batch, transition_batch

router = APIRouter(prefix="/api/batches", tags=["Batches"])


def _to_response(batch: Batch) -> dict:
    """Convert Batch ORM object to response dict with variety name."""
    return {
        **{c.key: getattr(batch, c.key) for c in batch.__table__.columns},
        "variety": batch.seed_inventory.variety,
    }


@router.get("/", response_model=list[BatchResponse])
def list_batches(
    status: Optional[str] = Query(None, description="Filter by status"),
    db: Session = Depends(get_db),
):
    query = db.query(Batch)
    if status:
        query = query.filter(Batch.status == status)
    batches = query.order_by(Batch.sow_date.desc()).all()
    return [_to_response(b) for b in batches]


@router.post("/", response_model=BatchResponse, status_code=201)
def create_new_batch(payload: BatchCreate, db: Session = Depends(get_db)):
    batch = create_batch(
        db,
        seed_inventory_id=payload.seed_inventory_id,
        sow_date=payload.sow_date,
        sowing_weight_g=float(payload.sowing_weight_g),
        notes=payload.notes,
    )
    return _to_response(batch)


@router.get("/{batch_id}", response_model=BatchResponse)
def get_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    return _to_response(batch)


@router.put("/{batch_id}", response_model=BatchResponse)
def update_batch(batch_id: int, payload: BatchUpdate, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(batch, field, value)
    db.commit()
    db.refresh(batch)
    return _to_response(batch)


@router.post("/{batch_id}/transition", response_model=BatchResponse)
def transition(batch_id: int, payload: BatchTransition, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    batch = transition_batch(
        db,
        batch=batch,
        new_status=payload.new_status,
        yield_weight_g=float(payload.yield_weight_g) if payload.yield_weight_g else None,
        mold_incident=payload.mold_incident,
        notes=payload.notes,
    )
    return _to_response(batch)


@router.delete("/{batch_id}", status_code=204)
def delete_batch(batch_id: int, db: Session = Depends(get_db)):
    batch = db.get(Batch, batch_id)
    if not batch:
        raise HTTPException(status_code=404, detail="Batch not found")
    db.delete(batch)
    db.commit()
