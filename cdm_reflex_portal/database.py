from __future__ import annotations

from pathlib import Path

import bcrypt
from sqlalchemy import DateTime, Float, String, Text, UniqueConstraint, create_engine, func, text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, sessionmaker

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
DATA_DIR.mkdir(exist_ok=True)
DB_PATH = DATA_DIR / "cdm.db"

engine = create_engine(f"sqlite:///{DB_PATH}", future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default="VIEWER")


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    cin: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    company_type: Mapped[str] = mapped_column(String(80), nullable=False)
    company_class: Mapped[str] = mapped_column(String(120), nullable=False)
    sub_category: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    date_of_incorporation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)


class Director(Base):
    __tablename__ = "directors"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    din: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


class CompanyDirector(Base):
    __tablename__ = "company_directors"
    __table_args__ = (UniqueConstraint("company_id", "director_id", name="uq_company_director"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(nullable=False)
    director_id: Mapped[int] = mapped_column(nullable=False)
    share_percent: Mapped[float | None] = mapped_column(Float, nullable=True)


def hash_password(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(value: str, hashed: str) -> bool:
    return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    # Migrate: add columns to existing databases
    with engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(companies)")).fetchall()]
        migrations = [
            ("sub_category", "ALTER TABLE companies ADD COLUMN sub_category VARCHAR(120)"),
            ("date_of_incorporation", "ALTER TABLE companies ADD COLUMN date_of_incorporation VARCHAR(20)"),
            ("email", "ALTER TABLE companies ADD COLUMN email VARCHAR(254)"),
            ("address", "ALTER TABLE companies ADD COLUMN address TEXT"),
        ]
        for col_name, ddl in migrations:
            if col_name not in cols:
                conn.execute(text(ddl))
                conn.commit()
    with SessionLocal() as session:
        admin = session.query(User).filter(User.username == "admin").first()
        if not admin:
            session.add(User(username="admin", password_hash=hash_password("admin123"), role="ADMIN"))
            session.commit()
