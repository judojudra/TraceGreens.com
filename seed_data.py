"""Seed the database with initial data for Radish and Pea Shoots."""

import sys
from datetime import date, timedelta
from decimal import Decimal

from app.config import settings  # noqa: F401 — triggers env loading
from app.database import Base, SessionLocal, engine
from app.models.batch import Batch
from app.models.customer import Customer
from app.models.order import Order
from app.models.seed_inventory import SeedInventory


def seed():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # Check if already seeded
        if db.query(SeedInventory).first():
            print("Database already has data. Skipping seed.")
            return

        # --- Seed Inventory ---
        radish = SeedInventory(
            variety="Radish",
            variety_code="RAD",
            supplier="Mumbai Seeds Co.",
            lot_number="RAD-2026-001",
            cost_per_kg=Decimal("800.00"),
            quantity_kg=Decimal("5.000"),
        )
        pea = SeedInventory(
            variety="Pea Shoots",
            variety_code="PEA",
            supplier="Mumbai Seeds Co.",
            lot_number="PEA-2026-001",
            cost_per_kg=Decimal("600.00"),
            quantity_kg=Decimal("3.000"),
        )
        db.add_all([radish, pea])
        db.flush()
        print(f"  Added seeds: Radish (id={radish.id}), Pea Shoots (id={pea.id})")

        # --- Batches ---
        today = date.today()

        # Batch 1: Radish — in Blackout (sowed today)
        b1 = Batch(
            batch_id=f"TG-RAD-{today.strftime('%Y%m%d')}-A",
            seed_inventory_id=radish.id,
            status="Blackout",
            sow_date=today,
            blackout_end_date=today + timedelta(days=3),
            harvest_target_start=today + timedelta(days=7),
            harvest_target_end=today + timedelta(days=9),
            sowing_weight_g=Decimal("25.0"),
        )

        # Batch 2: Radish — in Light (sowed 4 days ago)
        sow2 = today - timedelta(days=4)
        b2 = Batch(
            batch_id=f"TG-RAD-{sow2.strftime('%Y%m%d')}-A",
            seed_inventory_id=radish.id,
            status="Light",
            sow_date=sow2,
            blackout_end_date=sow2 + timedelta(days=3),
            harvest_target_start=sow2 + timedelta(days=7),
            harvest_target_end=sow2 + timedelta(days=9),
            sowing_weight_g=Decimal("25.0"),
        )

        # Batch 3: Pea Shoots — Harvested (sowed 10 days ago)
        sow3 = today - timedelta(days=10)
        b3 = Batch(
            batch_id=f"TG-PEA-{sow3.strftime('%Y%m%d')}-A",
            seed_inventory_id=pea.id,
            status="Harvested",
            sow_date=sow3,
            blackout_end_date=sow3 + timedelta(days=3),
            harvest_target_start=sow3 + timedelta(days=7),
            harvest_target_end=sow3 + timedelta(days=9),
            sowing_weight_g=Decimal("25.0"),
            yield_weight_g=Decimal("180.0"),
            actual_harvest_date=sow3 + timedelta(days=8),
        )

        db.add_all([b1, b2, b3])
        db.flush()
        print(f"  Added batches: {b1.batch_id}, {b2.batch_id}, {b3.batch_id}")

        # --- Customer ---
        customer = Customer(
            name="Chef Arjun Mehta",
            restaurant_name="Sage & Sprout",
            phone="+91-9876543210",
            email="arjun@sageandsprout.in",
        )
        db.add(customer)
        db.flush()
        print(f"  Added customer: {customer.name} ({customer.restaurant_name})")

        # --- Order ---
        order = Order(
            customer_id=customer.id,
            batch_id=b3.id,
            quantity_g=Decimal("150.0"),
            price_per_g=Decimal("1.6"),
            total_price=Decimal("240.00"),
        )
        db.add(order)
        print(f"  Added order: {order.quantity_g}g @ ₹{order.price_per_g}/g = ₹{order.total_price}")

        db.commit()
        print("\nDatabase seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
