import logging
from sqlalchemy import inspect
from app.db.database import engine

log = logging.getLogger("jeevanai.migrate")
OLD_TABLES = ["activity_logs", "pending_approvals", "documents", "tracked_products", "agent_permissions"]
NEW_USER_COLUMNS = {
    "role": "VARCHAR(20) NOT NULL DEFAULT 'user'",
    "phone": "VARCHAR(20)",
    "state": "VARCHAR(60)",
    "city": "VARCHAR(80)",
    "occupation": "VARCHAR(60)",
    "dob": "VARCHAR(10)",
    "is_active": "BOOLEAN NOT NULL DEFAULT TRUE",
    "last_login": "TIMESTAMP",
}


def migrate_legacy():
    """v0.1/v0.2 databases had no users. If found, drop those old (test) tables so v1 can recreate them."""
    insp = inspect(engine)
    if not insp.has_table("agent_permissions"):
        return
    cols = {c["name"] for c in insp.get_columns("agent_permissions")}
    if "user_id" in cols:
        return
    log.warning("Old database layout detected - recreating tables (old demo data is discarded).")
    with engine.begin() as conn:
        for t in OLD_TABLES:
            conn.exec_driver_sql(f"DROP TABLE IF EXISTS {t}")


def migrate_users():
    """Adds the profile/role columns to an existing users table (keeps all existing accounts)."""
    insp = inspect(engine)
    if not insp.has_table("users"):
        return
    have = {c["name"] for c in insp.get_columns("users")}
    with engine.begin() as conn:
        for col, ddl in NEW_USER_COLUMNS.items():
            if col not in have:
                log.info("Adding users.%s", col)
                conn.exec_driver_sql(f"ALTER TABLE users ADD COLUMN {col} {ddl}")
