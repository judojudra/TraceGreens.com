"""Admin routes — all behind password authentication."""

from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Cookie, Depends, File, Form, Query, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth import (
    COOKIE_VALUE,
    clear_admin_cookie,
    set_admin_cookie,
    verify_password,
)
from app.database import get_db
from app.models.batch import Batch
from app.models.batch_event import BatchEvent
from app.models.customer import Customer
from app.models.order import Order
from app.models.seed_inventory import SeedInventory
from app.services.batch_service import create_batch, transition_batch
from app.services.event_service import create_manual_event
from app.services.metrics_service import get_metrics, get_todo_items
from app.services.storage_service import r2_is_configured, upload_photo

router = APIRouter(prefix="/admin", tags=["Admin"])
templates = Jinja2Templates(directory="app/templates")


# --- Auth helpers ---

def _check_auth(tg_admin: str = Cookie(None)):
    if tg_admin != COOKIE_VALUE:
        return False
    return True


def _require_auth(tg_admin: str = Cookie(None)):
    if tg_admin != COOKIE_VALUE:
        return RedirectResponse("/admin/login", status_code=302)
    return None


@router.get("/login", response_class=HTMLResponse)
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@router.post("/login")
def login_submit(request: Request, password: str = Form(...)):
    if verify_password(password):
        response = RedirectResponse("/admin/", status_code=302)
        return set_admin_cookie(response)
    return templates.TemplateResponse("login.html", {"request": request, "error": "Incorrect password."})


@router.get("/logout")
def logout():
    response = RedirectResponse("/admin/login", status_code=302)
    return clear_admin_cookie(response)


# --- Dashboard ---

@router.get("/", response_class=HTMLResponse)
def dashboard(request: Request, tg_admin: str = Cookie(None), db: Session = Depends(get_db)):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    todos = get_todo_items(db)
    metrics = get_metrics(db)
    active_batches = db.query(Batch).filter(Batch.status.in_(["Blackout", "Light"])).order_by(Batch.sow_date.desc()).all()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "active_page": "dashboard",
        "need_light": todos["need_light"],
        "ready_harvest": todos["ready_harvest"],
        "metrics": metrics,
        "active_batches": active_batches,
        "today": date.today().strftime("%A, %d %B %Y"),
    })


# --- Batches ---

@router.get("/batches", response_class=HTMLResponse)
def batches_page(
    request: Request,
    status: str = Query(None),
    harvest: int = Query(None),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    query = db.query(Batch)
    if status:
        query = query.filter(Batch.status == status)
    batches = query.order_by(Batch.sow_date.desc()).all()

    seeds = db.query(SeedInventory).order_by(SeedInventory.variety).all()

    counts = {
        "all": db.query(func.count(Batch.id)).scalar() or 0,
        "blackout": db.query(func.count(Batch.id)).filter(Batch.status == "Blackout").scalar() or 0,
        "light": db.query(func.count(Batch.id)).filter(Batch.status == "Light").scalar() or 0,
        "harvested": db.query(func.count(Batch.id)).filter(Batch.status == "Harvested").scalar() or 0,
        "discarded": db.query(func.count(Batch.id)).filter(Batch.status == "Discarded").scalar() or 0,
    }

    # If coming from dashboard harvest link, get the batch info for auto-open
    harvest_batch_id = None
    if harvest:
        hb = db.get(Batch, harvest)
        if hb:
            harvest_batch_id = hb.batch_id

    return templates.TemplateResponse("batches.html", {
        "request": request,
        "active_page": "batches",
        "batches": batches,
        "seeds": seeds,
        "status_filter": status,
        "counts": counts,
        "today": date.today().isoformat(),
        "harvest_id": harvest,
        "harvest_batch_id": harvest_batch_id,
        "r2_available": r2_is_configured(),
    })


@router.post("/batches/create")
def create_batch_form(
    seed_inventory_id: int = Form(...),
    sow_date: date = Form(...),
    sowing_weight_g: float = Form(25.0),
    notes: str = Form(None),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    create_batch(db, seed_inventory_id, sow_date, sowing_weight_g, notes or None)
    return RedirectResponse("/admin/batches", status_code=302)


@router.post("/batches/{batch_id}/quick-transition")
def quick_transition(
    batch_id: int,
    new_status: str = Form(...),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    batch = db.get(Batch, batch_id)
    if batch:
        transition_batch(db, batch, new_status)
    return RedirectResponse("/admin/batches", status_code=302)


@router.post("/batches/{batch_id}/harvest")
def harvest_batch(
    batch_id: int,
    yield_weight_g: float = Form(...),
    mold_incident: str = Form(None),
    notes: str = Form(None),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    batch = db.get(Batch, batch_id)
    if batch:
        transition_batch(
            db, batch, "Harvested",
            yield_weight_g=yield_weight_g,
            mold_incident=mold_incident == "true",
            notes=notes or None,
        )
    return RedirectResponse("/admin/batches", status_code=302)


@router.post("/batches/{batch_id}/edit")
def edit_batch_form(
    batch_id: int,
    sowing_weight_g: float = Form(...),
    notes: str = Form(None),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    batch = db.get(Batch, batch_id)
    if batch and batch.status in ("Blackout", "Light"):
        batch.sowing_weight_g = Decimal(str(sowing_weight_g))
        batch.notes = notes or None
        db.commit()
    return RedirectResponse("/admin/batches", status_code=302)


@router.post("/batches/{batch_id}/delete")
def delete_batch(
    batch_id: int,
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    has_orders = db.query(Order).filter(Order.batch_id == batch_id).first()
    if has_orders:
        return RedirectResponse("/admin/batches", status_code=302)

    batch = db.get(Batch, batch_id)
    if batch:
        db.query(BatchEvent).filter(BatchEvent.batch_id == batch_id).delete()
        db.delete(batch)
        db.commit()
    return RedirectResponse("/admin/batches", status_code=302)


@router.post("/batches/{batch_id}/add-event")
async def add_event(
    batch_id: int,
    description: str = Form(...),
    photo: UploadFile = File(None),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    batch = db.get(Batch, batch_id)
    if not batch:
        return RedirectResponse("/admin/batches", status_code=302)

    photo_url = None
    if photo and photo.filename and r2_is_configured():
        photo_url = await upload_photo(photo)

    create_manual_event(db, batch.id, description, photo_url)
    return RedirectResponse("/admin/batches", status_code=302)


# --- Seed Inventory ---

@router.get("/inventory", response_class=HTMLResponse)
def inventory_page(request: Request, tg_admin: str = Cookie(None), db: Session = Depends(get_db)):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    seeds = db.query(SeedInventory).order_by(SeedInventory.variety).all()
    return templates.TemplateResponse("inventory.html", {
        "request": request,
        "active_page": "inventory",
        "seeds": seeds,
    })


@router.post("/inventory/create")
def create_seed_form(
    variety: str = Form(...),
    variety_code: str = Form(...),
    supplier: str = Form(...),
    lot_number: str = Form(...),
    cost_per_kg: float = Form(...),
    quantity_kg: float = Form(0),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    seed = SeedInventory(
        variety=variety,
        variety_code=variety_code.upper(),
        supplier=supplier,
        lot_number=lot_number,
        cost_per_kg=Decimal(str(cost_per_kg)),
        quantity_kg=Decimal(str(quantity_kg)),
    )
    db.add(seed)
    db.commit()
    return RedirectResponse("/admin/inventory", status_code=302)


@router.post("/inventory/{seed_id}/edit")
def edit_seed_form(
    seed_id: int,
    variety: str = Form(...),
    variety_code: str = Form(...),
    supplier: str = Form(...),
    lot_number: str = Form(...),
    cost_per_kg: float = Form(...),
    quantity_kg: float = Form(0),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    seed = db.get(SeedInventory, seed_id)
    if seed:
        seed.variety = variety
        seed.variety_code = variety_code.upper()
        seed.supplier = supplier
        seed.lot_number = lot_number
        seed.cost_per_kg = Decimal(str(cost_per_kg))
        seed.quantity_kg = Decimal(str(quantity_kg))
        db.commit()
    return RedirectResponse("/admin/inventory", status_code=302)


@router.post("/inventory/{seed_id}/delete")
def delete_seed(
    seed_id: int,
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    has_batches = db.query(Batch).filter(Batch.seed_inventory_id == seed_id).first()
    if has_batches:
        return RedirectResponse("/admin/inventory", status_code=302)

    seed = db.get(SeedInventory, seed_id)
    if seed:
        db.delete(seed)
        db.commit()
    return RedirectResponse("/admin/inventory", status_code=302)


# --- Customers ---

@router.get("/customers", response_class=HTMLResponse)
def customers_page(request: Request, tg_admin: str = Cookie(None), db: Session = Depends(get_db)):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    customers = db.query(Customer).order_by(Customer.name).all()
    return templates.TemplateResponse("customers.html", {
        "request": request,
        "active_page": "customers",
        "customers": customers,
    })


@router.post("/customers/create")
def create_customer_form(
    name: str = Form(...),
    restaurant_name: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    customer = Customer(
        name=name,
        restaurant_name=restaurant_name or None,
        phone=phone or None,
        email=email or None,
    )
    db.add(customer)
    db.commit()
    return RedirectResponse("/admin/customers", status_code=302)


@router.post("/customers/{customer_id}/edit")
def edit_customer_form(
    customer_id: int,
    name: str = Form(...),
    restaurant_name: str = Form(None),
    phone: str = Form(None),
    email: str = Form(None),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    customer = db.get(Customer, customer_id)
    if customer:
        customer.name = name
        customer.restaurant_name = restaurant_name or None
        customer.phone = phone or None
        customer.email = email or None
        db.commit()
    return RedirectResponse("/admin/customers", status_code=302)


@router.post("/customers/{customer_id}/delete")
def delete_customer(
    customer_id: int,
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    has_orders = db.query(Order).filter(Order.customer_id == customer_id).first()
    if has_orders:
        return RedirectResponse("/admin/customers", status_code=302)

    customer = db.get(Customer, customer_id)
    if customer:
        db.delete(customer)
        db.commit()
    return RedirectResponse("/admin/customers", status_code=302)


# --- Orders ---

@router.get("/orders", response_class=HTMLResponse)
def orders_page(request: Request, tg_admin: str = Cookie(None), db: Session = Depends(get_db)):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    orders = db.query(Order).order_by(Order.order_date.desc()).all()
    customers = db.query(Customer).order_by(Customer.name).all()
    harvested_batches = db.query(Batch).filter(Batch.status == "Harvested").order_by(Batch.sow_date.desc()).all()

    total_revenue = db.query(func.sum(Order.total_price)).scalar() or Decimal("0")

    return templates.TemplateResponse("orders.html", {
        "request": request,
        "active_page": "orders",
        "orders": orders,
        "customers": customers,
        "harvested_batches": harvested_batches,
        "total_orders": len(orders),
        "total_revenue": total_revenue,
    })


@router.post("/orders/create")
def create_order_form(
    customer_id: int = Form(...),
    batch_id: int = Form(...),
    quantity_g: float = Form(...),
    price_per_g: float = Form(1.6),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    total_price = Decimal(str(quantity_g)) * Decimal(str(price_per_g))
    order = Order(
        customer_id=customer_id,
        batch_id=batch_id,
        quantity_g=Decimal(str(quantity_g)),
        price_per_g=Decimal(str(price_per_g)),
        total_price=total_price,
    )
    db.add(order)
    db.commit()
    return RedirectResponse("/admin/orders", status_code=302)


@router.post("/orders/{order_id}/edit")
def edit_order_form(
    order_id: int,
    quantity_g: float = Form(...),
    price_per_g: float = Form(...),
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    order = db.get(Order, order_id)
    if order:
        order.quantity_g = Decimal(str(quantity_g))
        order.price_per_g = Decimal(str(price_per_g))
        order.total_price = Decimal(str(quantity_g)) * Decimal(str(price_per_g))
        db.commit()
    return RedirectResponse("/admin/orders", status_code=302)


@router.post("/orders/{order_id}/delete")
def delete_order(
    order_id: int,
    tg_admin: str = Cookie(None),
    db: Session = Depends(get_db),
):
    redirect = _require_auth(tg_admin)
    if redirect:
        return redirect

    order = db.get(Order, order_id)
    if order:
        db.delete(order)
        db.commit()
    return RedirectResponse("/admin/orders", status_code=302)
