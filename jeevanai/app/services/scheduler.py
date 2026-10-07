"""Background job: re-check prices of products that have an alert, create notifications."""
import asyncio
import logging
from sqlalchemy import select
from app.core.config import settings
from app.db.database import SessionLocal
from app.db.models import TrackedProduct
from app.agents.shopping import maybe_notify, refresh_product

log = logging.getLogger("jeevanai.scheduler")


def run_once() -> int:
    db = SessionLocal()
    checked = 0
    try:
        products = db.scalars(select(TrackedProduct).where(TrackedProduct.alert_enabled.is_(True))).all()
        for p in products:
            try:
                refresh_product(db, p)
                maybe_notify(db, p)
                checked += 1
            except Exception as e:  # one bad site must not stop the others
                db.rollback()
                log.warning("Price check failed for product %s: %s", p.id, e)
    finally:
        db.close()
    return checked


async def price_loop():
    interval = max(1, settings.price_check_minutes) * 60
    while True:
        await asyncio.sleep(interval)
        try:
            await asyncio.to_thread(run_once)
        except Exception:
            log.exception("Scheduler run failed")
