from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.seed_inventory import SeedInventory
from app.schemas.seed_inventory import (
    SeedInventoryCreate,
    SeedInventoryResponse,
    SeedInventoryUpdate,
)

router = APIRouter(prefix="/api/seeds", tags=["Seed Inventory"])


@router.get("/", response_model=list[SeedInventoryResponse])
def list_seeds(db: Session = Depends(get_db)):
    return db.query(SeedInventory).order_by(SeedInventory.variety).all()


@router.post("/", response_model=SeedInventoryResponse, status_code=201)
def create_seed(payload: SeedInventoryCreate, db: Session = Depends(get_db)):
    existing = db.query(SeedInventory).filter_by(variety_code=payload.variety_code).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Variety code '{payload.variety_code}' already exists")
    seed = SeedInventory(**payload.model_dump())
    db.add(seed)
    db.commit()
    db.refresh(seed)
    return seed


@router.get("/{seed_id}", response_model=SeedInventoryResponse)
def get_seed(seed_id: int, db: Session = Depends(get_db)):
    seed = db.get(SeedInventory, seed_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found")
    return seed


@router.put("/{seed_id}", response_model=SeedInventoryResponse)
def update_seed(seed_id: int, payload: SeedInventoryUpdate, db: Session = Depends(get_db)):
    seed = db.get(SeedInventory, seed_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(seed, field, value)
    db.commit()
    db.refresh(seed)
    return seed


@router.delete("/{seed_id}", status_code=204)
def delete_seed(seed_id: int, db: Session = Depends(get_db)):
    seed = db.get(SeedInventory, seed_id)
    if not seed:
        raise HTTPException(status_code=404, detail="Seed not found")
    db.delete(seed)
    db.commit()
