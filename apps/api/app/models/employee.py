import uuid
from datetime import date, datetime

from sqlalchemy import DateTime, Enum, ForeignKey, UniqueConstraint, text
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import EmployeeRole


class Employee(Base):
    __tablename__ = "employees"
    __table_args__ = (
        UniqueConstraint("company_id", "employee_code", name="uq_employees_company_employee_code"),
        UniqueConstraint("company_id", "phone", name="uq_employees_company_phone"),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"))
    location_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("locations.id"))
    employee_code: Mapped[str]
    first_name: Mapped[str]
    last_name: Mapped[str]
    phone: Mapped[str]
    email: Mapped[str | None]
    password_hash: Mapped[str | None]
    role: Mapped[EmployeeRole] = mapped_column(Enum(EmployeeRole, native_enum=False, length=32))
    job_title_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("job_titles.id"))
    address: Mapped[str | None]
    emergency_contact_name: Mapped[str | None]
    emergency_contact_phone: Mapped[str | None]
    photo_url: Mapped[str | None]
    start_date: Mapped[date]
    end_date: Mapped[date | None]
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
