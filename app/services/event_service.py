"""Service for creating batch events (auto and manual)."""

from sqlalchemy.orm import Session

from app.models.batch_event import BatchEvent


def log_auto_event(db: Session, batch_id: int, description: str) -> BatchEvent:
    """Create an automatic system event. Does NOT commit — caller owns the transaction."""
    event = BatchEvent(
        batch_id=batch_id,
        event_type="auto",
        description=description,
    )
    db.add(event)
    return event


def create_manual_event(
    db: Session,
    batch_id: int,
    description: str,
    photo_url: str | None = None,
) -> BatchEvent:
    """Create a manual journal entry event. Commits immediately."""
    event = BatchEvent(
        batch_id=batch_id,
        event_type="manual",
        description=description,
        photo_url=photo_url,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return event
