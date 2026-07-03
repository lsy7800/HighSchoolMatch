"""SQLite engine and session management."""
from pathlib import Path

from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# DB lives at backend/data/app.db (gitignored; created by seed script)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "app.db"

engine = create_engine(
    f"sqlite:///{DB_PATH}",
    connect_args={"check_same_thread": False},
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency: yields a session, always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def _ensure_schema(engine):
    """轻量迁移: create_all 不会给已有表补列/删列, 这里手动对齐 school 表字段。"""
    with engine.connect() as conn:
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(school)"))}
        # 新增列(新数据源引入)
        for col, ddl in [
            ("subject_model", "ALTER TABLE school ADD COLUMN subject_model TEXT"),
            ("class_adjust", "ALTER TABLE school ADD COLUMN class_adjust TEXT"),
            ("schedule", "ALTER TABLE school ADD COLUMN schedule TEXT"),
            ("fee_reduction", "ALTER TABLE school ADD COLUMN fee_reduction TEXT"),
            ("other_info", "ALTER TABLE school ADD COLUMN other_info TEXT"),
            ("intro", "ALTER TABLE school ADD COLUMN intro TEXT"),
        ]:
            if col not in cols:
                conn.execute(text(ddl))
        # 删除列(新数据源不再含; SQLite 3.35+ 支持 DROP COLUMN, 失败则留为孤儿列无害)
        conn.commit()
        cols = {row[1] for row in conn.execute(text("PRAGMA table_info(school)"))}
        for col in ("home_district", "recruit_area", "dorm_fee", "address", "phone"):
            if col in cols:
                try:
                    conn.execute(text(f"ALTER TABLE school DROP COLUMN {col}"))
                except Exception:
                    pass  # 老 SQLite 不支持, 留为孤儿列(模型不再引用, 无害)
        conn.commit()


def init_db():
    """Create all tables. Import models first so they register on Base."""
    from . import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    _ensure_schema(engine)
