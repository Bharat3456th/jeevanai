import asyncio
import logging
import time
from app.agents.shopping import refresh_product
from app.db.database import SessionLocal
from app.db.models import TrackedProduct

log = logging.getLogger("jeevanai.scheduler")


def check_all_products():
    db = SessionLocal()
    try:
        ids = [i for (i,) in db.query(TrackedProduct.id).all()]
        for pid in ids:
            p = db.get(TrackedProduct, pid)
            if not p:
                continue
            try:
                refresh_product(db, p)
            except Exception as e:  # noqa: BLE001
                db.rollback()
                log.warning("Price check failed for product %s: %s", pid, e)
            time.sleep(1)
    finally:
        db.close()


async def price_loop(minutes: int):
    while True:
        await asyncio.sleep(minutes * 60)
        try:
            await asyncio.to_thread(check_all_products)
        except Exception:  # noqa: BLE001
            log.exception("Price loop error")
