from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from app.database import get_db
from app.services.metrics_service import get_metrics, get_todo_items

router = APIRouter(tags=["Dashboard"])
templates = Jinja2Templates(directory="app/templates")


@router.get("/dashboard", response_class=HTMLResponse)
def dashboard(request: Request, db: Session = Depends(get_db)):
    todos = get_todo_items(db)
    metrics = get_metrics(db)
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "need_light": todos["need_light"],
        "ready_harvest": todos["ready_harvest"],
        "metrics": metrics,
    })
