from datetime import datetime, timezone
from typing import Optional, Tuple
from sqlalchemy import func, select
from app.db.models import Notification, TrackedProduct
from app.agents.pricing import is_safe_url, parse_price

MAX_PRODUCTS = 50


def fetch_price(url: str) -> Optional[Tuple[float, str]]:
    """Download the page (following up to 3 safe redirects) and parse the price."""
    import httpx
    for _ in range(4):
        if not is_safe_url(url):
            raise ValueError("This URL is not allowed.")
        try:
            r = httpx.get(url, timeout=15, follow_redirects=False,
                          headers={"User-Agent": "Mozilla/5.0 JeevanAI-PriceCheck"})
            if r.is_redirect and r.headers.get("location"):
                url = str(httpx.URL(url).join(r.headers["location"]))
                continue
            r.raise_for_status()
        except httpx.HTTPError as e:
            raise ValueError(f"Could not fetch the page: {e}")
        return parse_price(r.text[:2_000_000])
    raise ValueError("Too many redirects.")


def refresh_product(db, p: TrackedProduct) -> bool:
    found = fetch_price(p.url)
    p.last_checked = datetime.now(timezone.utc)
    if found:
        p.last_price, p.currency = found
    db.commit()
    return bool(found)


def target_reached(p: TrackedProduct) -> bool:
    return bool(p.target_price and p.last_price is not None and p.last_price <= p.target_price)


def maybe_notify(db, p: TrackedProduct) -> bool:
    if p.alert_enabled and target_reached(p) and p.notified_price != p.last_price:
        db.add(Notification(user_id=p.user_id, title=f"Price alert: {p.name or 'your product'}",
                            body=f"Now {p.last_price} {p.currency} (target {p.target_price}). {p.url}"))
        p.notified_price = p.last_price
        db.commit()
        return True
    return False


def _product(ctx) -> TrackedProduct:
    try:
        pid = int(ctx.payload.get("product_id"))
    except (TypeError, ValueError):
        raise ValueError("Choose a product (track one first).")
    p = ctx.db.scalar(select(TrackedProduct).where(TrackedProduct.id == pid, TrackedProduct.user_id == ctx.user_id))
    if not p:
        raise ValueError("Product not found.")
    return p


def _target(value) -> Optional[float]:
    if value in (None, ""):
        return None
    try:
        t = float(value)
    except (TypeError, ValueError):
        raise ValueError("Target price must be a number.")
    if t <= 0:
        raise ValueError("Target price must be positive.")
    return t


def track_product(ctx):
    url = (ctx.payload.get("url") or "").strip()
    if not is_safe_url(url):
        raise ValueError("Provide a valid public http(s) product URL.")
    count = ctx.db.scalar(select(func.count()).select_from(TrackedProduct).where(TrackedProduct.user_id == ctx.user_id))
    if (count or 0) >= MAX_PRODUCTS:
        raise ValueError(f"You can track at most {MAX_PRODUCTS} products.")
    p = TrackedProduct(user_id=ctx.user_id, url=url, name=str(ctx.payload.get("name") or "")[:200],
                       target_price=_target(ctx.payload.get("target_price")))
    ctx.db.add(p)
    ctx.db.commit()
    ctx.db.refresh(p)
    return {"response": f"Tracking product #{p.id}.", "data": {"product_id": p.id}, "mode": "live"}


def check_price(ctx):
    p = _product(ctx)
    if not refresh_product(ctx.db, p):
        return {"response": "Price not found on this page (the site may load prices with JavaScript).",
                "data": {"product_id": p.id}, "mode": "live"}
    notified = maybe_notify(ctx.db, p)
    reached = target_reached(p)
    return {"response": f"Current price: {p.last_price} {p.currency}" + (" - TARGET REACHED!" if reached else ""),
            "data": {"product_id": p.id, "price": p.last_price, "currency": p.currency,
                     "target_reached": reached, "notification_created": notified}, "mode": "live"}


def set_price_alert(ctx):
    p = _product(ctx)
    target = _target(ctx.payload.get("target_price"))
    if target is None:
        raise ValueError("Enter a target price.")
    p.target_price, p.alert_enabled, p.notified_price = target, True, None
    ctx.db.commit()
    return {"response": f"Alert set at {target} for product #{p.id}. You will see it in Alerts.",
            "data": {"product_id": p.id, "target_price": target}, "mode": "live"}


def purchase(ctx):
    # Intentionally not implemented: there is no payment integration. Even if the permission is
    # changed to ALLOW, this agent will never spend money.
    raise ValueError("Purchasing is not supported. Open the product link and buy manually.")
