"""Public-facing routes — no auth required."""

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.models.batch import Batch
from app.models.batch_event import BatchEvent
from app.services.metrics_service import get_metrics

router = APIRouter(tags=["Public"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/favicon.ico", include_in_schema=False)
@router.head("/favicon.ico", include_in_schema=False)
def favicon_ico():
    return FileResponse("app/static/favicon.ico")


@router.get("/favicon.svg", include_in_schema=False)
@router.head("/favicon.svg", include_in_schema=False)
def favicon_svg():
    return FileResponse("app/static/favicon.svg")


@router.get("/favicon.png", include_in_schema=False)
@router.head("/favicon.png", include_in_schema=False)
def favicon_png():
    return FileResponse("app/static/favicon.png")


@router.get("/apple-touch-icon.png", include_in_schema=False)
@router.head("/apple-touch-icon.png", include_in_schema=False)
def apple_touch_icon():
    return FileResponse("app/static/apple-touch-icon.png")




@router.get("/", response_class=HTMLResponse, include_in_schema=False)
@router.head("/", response_class=HTMLResponse, include_in_schema=False)
def homepage(
    request: Request,
    batch_id: str = Query(None),
    db: Session = Depends(get_db),
):
    """Public homepage with hero, about, gallery, trace, contact."""
    metrics = get_metrics(db)

    # Gallery: latest batch photos (6 for a clean 3x2 grid)
    gallery_photos = (
        db.query(BatchEvent)
        .options(joinedload(BatchEvent.batch))
        .filter(BatchEvent.photo_url.isnot(None))
        .order_by(BatchEvent.created_at.desc())
        .limit(6)
        .all()
    )

    context = {
        "request": request,
        "metrics": metrics,
        "batch": None,
        "trace_error": None,
        "query": batch_id,
        "gallery_photos": gallery_photos,
    }

    if batch_id:
        batch = (
            db.query(Batch)
            .options(joinedload(Batch.events))
            .filter(Batch.batch_id == batch_id.strip().upper())
            .first()
        )
        if batch:
            context["batch"] = batch
        else:
            context["trace_error"] = f"No batch found with ID '{batch_id}'. Check the format: TG-RAD-20260209-A"

    return templates.TemplateResponse("home.html", context)


@router.get("/trace", response_class=HTMLResponse, include_in_schema=False)
def trace_redirect(batch_id: str = Query(None)):
    """Redirect /trace to homepage trace section."""
    if batch_id:
        return RedirectResponse(f"/?batch_id={batch_id}#trace", status_code=302)
    return RedirectResponse("/#trace", status_code=302)


@router.get("/trace/{batch_id}", response_class=HTMLResponse, include_in_schema=False)
def trace_by_path(batch_id: str):
    """Direct link to trace a specific batch."""
    return RedirectResponse(f"/?batch_id={batch_id}#trace", status_code=302)


@router.post("/enquiry", include_in_schema=False)
def enquiry_submit():
    """Handle contact form — for now redirect with thanks."""
    return RedirectResponse("/?thanks=1#order", status_code=302)
