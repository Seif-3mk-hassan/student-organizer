"""DB init: user-data dir + WAL + check_same_thread=False + per-request session."""
from pathlib import Path
import platformdirs
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

APP_NAME = "student-organizer"
APP_AUTHOR = "student-organizer"

def get_user_data_dir() -> Path:
    p = Path(platformdirs.user_data_dir(APP_NAME, APP_AUTHOR))
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_db_path() -> Path:
    return get_user_data_dir() / "app.db"

def get_materials_root() -> Path:
    p = get_user_data_dir() / "materials"
    p.mkdir(parents=True, exist_ok=True)
    return p

def get_db_url() -> str:
    return f"sqlite:///{get_db_path().as_posix()}"

class Base(DeclarativeBase):
    pass

engine = create_engine(
    get_db_url(),
    connect_args={"check_same_thread": False},
    echo=False,
)

@event.listens_for(engine, "connect")
def _set_sqlite_pragma(dbapi_conn, _):
    cur = dbapi_conn.cursor()
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.execute("PRAGMA foreign_keys=ON;")
    cur.close()

# auto-migrate missing columns/tables for existing DBs (no Alembic run needed)
def _auto_migrate():
    import sqlite3
    db_path = get_db_path()
    if not db_path.exists():
        return
    try:
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        # courses.allowed_absences
        cur.execute("PRAGMA table_info(courses)")
        cols = {r[1] for r in cur.fetchall()}
        if "allowed_absences" not in cols:
            cur.execute("ALTER TABLE courses ADD COLUMN allowed_absences INTEGER DEFAULT 3 NOT NULL")
        # assignments.snoozed_until
        cur.execute("PRAGMA table_info(assignments)")
        cols = {r[1] for r in cur.fetchall()}
        if "snoozed_until" not in cols:
            cur.execute("ALTER TABLE assignments ADD COLUMN snoozed_until DATETIME")
        conn.commit()
        conn.close()
    except Exception:
        pass

_auto_migrate()

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
