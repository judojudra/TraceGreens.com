from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.batch import Batch, TRANSITIONS
from app.models.seed_inventory import SeedInventory
from app.services.event_service import log_auto_event


def generate_batch_id(db: Session, variety_code: str, sow_date: date) -> str:
    """Generate batch ID like TG-RAD-20260209-A, auto-incrementing the suffix."""
    date_str = sow_date.strftime("%Y%m%d")
    prefix = f"TG-{variety_code}-{date_str}-"

    existing = (
        db.query(Batch)
        .filter(Batch.batch_id.like(f"{prefix}%"))
        .order_by(Batch.batch_id.desc())
        .first()
    )

    if existing:
        last_suffix = existing.batch_id[-1]
        next_suffix = chr(ord(last_suffix) + 1)
    else:
        next_suffix = "A"

    return f"{prefix}{next_suffix}"


def calculate_dates(sow_date: date) -> dict:
    """Calculate lifecycle dates from sow date."""
    return {
        "blackout_end_date": sow_date + timedelta(days=3),
        "harvest_target_start": sow_date + timedelta(days=7),
        "harvest_target_end": sow_date + timedelta(days=9),
    }


def create_batch(db: Session, seed_inventory_id: int, sow_date: date, sowing_weight_g: float, notes: str | None) -> Batch:
    """Create a new batch with auto-generated ID and calculated dates."""
    seed = db.get(SeedInventory, seed_inventory_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Seed inventory not found")

    batch_id = generate_batch_id(db, seed.variety_code, sow_date)
    dates = calculate_dates(sow_date)

    batch = Batch(
        batch_id=batch_id,
        seed_inventory_id=seed_inventory_id,
        sow_date=sow_date,
        sowing_weight_g=sowing_weight_g,
        notes=notes,
        **dates,
    )
    db.add(batch)
    db.flush()  # Get batch.id for the event FK
    log_auto_event(
        db, batch.id,
        f"Batch created — {batch.sowing_weight_g}g of {seed.variety} seed sown",
    )
    db.commit()
    db.refresh(batch)
    return batch


def transition_batch(
    db: Session,
    batch: Batch,
    new_status: str,
    yield_weight_g: float | None = None,
    mold_incident: bool | None = None,
    notes: str | None = None,
) -> Batch:
    """Transition a batch to a new status with validation."""
    allowed = TRANSITIONS.get(batch.status, [])
    if new_status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from '{batch.status}' to '{new_status}'. Allowed: {allowed}",
        )

    if new_status == "Harvested" and yield_weight_g is None:
        raise HTTPException(status_code=400, detail="yield_weight_g is required when harvesting")

    batch.status = new_status

    if new_status == "Harvested":
        batch.yield_weight_g = yield_weight_g
        batch.actual_harvest_date = date.today()

    if mold_incident is not None:
        batch.mold_incident = mold_incident

    if notes is not None:
        batch.notes = notes

    # Log auto-event for the transition
    if new_status == "Light":
        log_auto_event(db, batch.id, "Moved to light phase")
    elif new_status == "Harvested":
        desc = f"Harvested — {yield_weight_g}g yield"
        if mold_incident:
            desc += " (mold incident reported)"
        log_auto_event(db, batch.id, desc)
    elif new_status == "Discarded":
        desc = "Batch discarded"
        if notes:
            desc += f" — {notes}"
        log_auto_event(db, batch.id, desc)

    db.commit()
    db.refresh(batch)
    return batch
