from __future__ import annotations

from pathlib import Path

import bcrypt
from sqlalchemy import DateTime, String, Text, create_engine, func
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
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    state: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())


def hash_password(value: str) -> str:
    return bcrypt.hashpw(value.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(value: str, hashed: str) -> bool:
    return bcrypt.checkpw(value.encode("utf-8"), hashed.encode("utf-8"))


def init_db() -> None:
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as session:
        admin = session.query(User).filter(User.username == "admin").first()
        if not admin:
            session.add(User(username="admin", password_hash=hash_password("admin123"), role="ADMIN"))
            session.commit()
