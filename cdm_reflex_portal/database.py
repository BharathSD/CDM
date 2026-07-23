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
    # Extended MCA fields
    roc_code: Mapped[str | None] = mapped_column(String(140), nullable=True)  # ROC Name
    roc_office: Mapped[str | None] = mapped_column(String(100), nullable=True)
    rd_name: Mapped[str | None] = mapped_column(String(140), nullable=True)
    rd_region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    registration_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    authorised_capital: Mapped[float | None] = mapped_column(Float, nullable=True)
    paid_up_capital: Mapped[float | None] = mapped_column(Float, nullable=True)
    number_of_members: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_last_agm: Mapped[str | None] = mapped_column(String(20), nullable=True)
    date_of_balance_sheet: Mapped[str | None] = mapped_column(String(20), nullable=True)
    listed_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    suspended_at_stock_exchange: Mapped[str | None] = mapped_column(String(10), nullable=True)
    pin_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    country: Mapped[str | None] = mapped_column(String(60), nullable=True)


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
    designation: Mapped[str | None] = mapped_column(String(60), nullable=True)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    original_appointment_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    current_designation_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cessation_date: Mapped[str | None] = mapped_column(String(20), nullable=True)


class LLP(Base):
    __tablename__ = "llps"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    llpin: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(140), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="active", nullable=False)
    updated_at: Mapped[str] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())
    roc_name: Mapped[str | None] = mapped_column(String(140), nullable=True)
    date_of_incorporation: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(254), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    number_of_partners: Mapped[str | None] = mapped_column(String(20), nullable=True)
    number_of_designated_partners: Mapped[str | None] = mapped_column(String(20), nullable=True)
    total_obligation_of_contribution: Mapped[float | None] = mapped_column(Float, nullable=True)
    strike_off_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status_under_cirp: Mapped[str | None] = mapped_column(String(10), nullable=True)
    small_llp: Mapped[str | None] = mapped_column(String(10), nullable=True)


class LLPDirector(Base):
    __tablename__ = "llp_directors"
    __table_args__ = (UniqueConstraint("llp_id", "director_id", name="uq_llp_director"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    llp_id: Mapped[int] = mapped_column(nullable=False)
    director_id: Mapped[int] = mapped_column(nullable=False)
    designation: Mapped[str | None] = mapped_column(String(60), nullable=True)
    appointment_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    cessation_date: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_signatory: Mapped[str | None] = mapped_column(String(10), nullable=True)


class CompanyLLP(Base):
    __tablename__ = "company_llps"
    __table_args__ = (UniqueConstraint("company_id", "llp_id", name="uq_company_llp"),)

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    company_id: Mapped[int] = mapped_column(nullable=False)
    llp_id: Mapped[int] = mapped_column(nullable=False)
    relationship_note: Mapped[str | None] = mapped_column(String(140), nullable=True)


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
            ("roc_code", "ALTER TABLE companies ADD COLUMN roc_code VARCHAR(140)"),
            ("roc_office", "ALTER TABLE companies ADD COLUMN roc_office VARCHAR(100)"),
            ("rd_name", "ALTER TABLE companies ADD COLUMN rd_name VARCHAR(140)"),
            ("rd_region", "ALTER TABLE companies ADD COLUMN rd_region VARCHAR(100)"),
            ("registration_number", "ALTER TABLE companies ADD COLUMN registration_number VARCHAR(20)"),
            ("authorised_capital", "ALTER TABLE companies ADD COLUMN authorised_capital FLOAT"),
            ("paid_up_capital", "ALTER TABLE companies ADD COLUMN paid_up_capital FLOAT"),
            ("number_of_members", "ALTER TABLE companies ADD COLUMN number_of_members VARCHAR(20)"),
            ("date_of_last_agm", "ALTER TABLE companies ADD COLUMN date_of_last_agm VARCHAR(20)"),
            ("date_of_balance_sheet", "ALTER TABLE companies ADD COLUMN date_of_balance_sheet VARCHAR(20)"),
            ("listed_status", "ALTER TABLE companies ADD COLUMN listed_status VARCHAR(20)"),
            ("suspended_at_stock_exchange", "ALTER TABLE companies ADD COLUMN suspended_at_stock_exchange VARCHAR(10)"),
            ("pin_code", "ALTER TABLE companies ADD COLUMN pin_code VARCHAR(10)"),
            ("phone", "ALTER TABLE companies ADD COLUMN phone VARCHAR(20)"),
            ("country", "ALTER TABLE companies ADD COLUMN country VARCHAR(60)"),
        ]
        for col_name, ddl in migrations:
            if col_name not in cols:
                conn.execute(text(ddl))
                conn.commit()
        cd_cols = [row[1] for row in conn.execute(text("PRAGMA table_info(company_directors)")).fetchall()]
        cd_migrations = [
            ("designation", "ALTER TABLE company_directors ADD COLUMN designation VARCHAR(60)"),
            ("category", "ALTER TABLE company_directors ADD COLUMN category VARCHAR(60)"),
            ("original_appointment_date", "ALTER TABLE company_directors ADD COLUMN original_appointment_date VARCHAR(20)"),
            ("current_designation_date", "ALTER TABLE company_directors ADD COLUMN current_designation_date VARCHAR(20)"),
            ("cessation_date", "ALTER TABLE company_directors ADD COLUMN cessation_date VARCHAR(20)"),
        ]
        for col_name, ddl in cd_migrations:
            if col_name not in cd_cols:
                conn.execute(text(ddl))
                conn.commit()
    with SessionLocal() as session:
        admin = session.query(User).filter(User.username == "admin").first()
        if not admin:
            session.add(User(username="admin", password_hash=hash_password("admin123"), role="ADMIN"))
            session.commit()
