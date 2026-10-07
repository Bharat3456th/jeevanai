from pathlib import Path
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import declarative_base, sessionmaker
from app.core.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}
engine = create_engine(settings.database_url, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_schema():
    """v0.x databases have no users. Back the old SQLite file up and start fresh."""
    insp = inspect(engine)
    if "agent_permissions" not in insp.get_table_names():
        return
    if "user_id" in {c["name"] for c in insp.get_columns("agent_permissions")}:
        return
    url = engine.url
    if url.get_backend_name() == "sqlite" and url.database and url.database != ":memory:":
        engine.dispose()
        src = Path(url.database)
        dst = src.with_name(src.name + ".old-backup")
        n = 1
        while dst.exists():
            dst = src.with_name(f"{src.name}.old-backup{n}")
            n += 1
        src.rename(dst)
        print(f"[JeevanAI] Old database backed up as {dst.name}; creating a fresh one.")
    else:
        raise RuntimeError("Old database schema detected. Use a new DATABASE_URL or migrate manually.")
