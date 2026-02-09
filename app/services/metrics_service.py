from datetime import date

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.batch import Batch


def get_todo_items(db: Session) -> dict:
    """Get batches that need action today."""
    today = date.today()

    need_light = (
        db.query(Batch)
        .filter(Batch.status == "Blackout", Batch.blackout_end_date <= today)
        .order_by(Batch.blackout_end_date)
        .all()
    )

    ready_harvest = (
        db.query(Batch)
        .filter(Batch.status == "Light", Batch.harvest_target_start <= today)
        .order_by(Batch.harvest_target_start)
        .all()
    )

    return {"need_light": need_light, "ready_harvest": ready_harvest}


def get_metrics(db: Session) -> dict:
    """Calculate mold rate and average yield."""
    past_blackout = (
        db.query(func.count(Batch.id))
        .filter(Batch.status != "Blackout")
        .scalar()
    ) or 0

    mold_count = (
        db.query(func.count(Batch.id))
        .filter(Batch.status != "Blackout", Batch.mold_incident.is_(True))
        .scalar()
    ) or 0

    mold_rate = (mold_count / past_blackout * 100) if past_blackout > 0 else 0.0

    avg_yield = (
        db.query(func.avg(Batch.yield_weight_g))
        .filter(Batch.status == "Harvested")
        .scalar()
    )
    avg_yield = float(avg_yield) if avg_yield else 0.0

    total_batches = db.query(func.count(Batch.id)).scalar() or 0

    active_batches = (
        db.query(func.count(Batch.id))
        .filter(Batch.status.in_(["Blackout", "Light"]))
        .scalar()
    ) or 0

    harvested_count = (
        db.query(func.count(Batch.id))
        .filter(Batch.status == "Harvested")
        .scalar()
    ) or 0

    return {
        "mold_rate": round(mold_rate, 1),
        "mold_ok": mold_rate < 5.0,
        "avg_yield_g": round(avg_yield, 1),
        "total_batches": total_batches,
        "active_batches": active_batches,
        "harvested_count": harvested_count,
    }
