import uuid
from datetime import UTC, date, datetime

from sqlalchemy import (
    DateTime,
    Enum,
    ForeignKey,
    UniqueConstraint,
    event,
    inspect,
    text,
    update,
)
from sqlalchemy.orm import Mapped, Session, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base
from app.models.enums import EmployeeRole
from app.models.refresh_token import RefreshToken


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


@event.listens_for(Session, "before_flush")
def _revoke_refresh_tokens_on_deactivation(session, flush_context, instances):
    for obj in session.dirty:
        if not isinstance(obj, Employee):
            continue
        history = inspect(obj).attrs.is_active.history
        if history.has_changes() and obj.is_active is False:
            session.execute(
                update(RefreshToken)
                .where(RefreshToken.employee_id == obj.id, RefreshToken.revoked_at.is_(None))
                .values(revoked_at=datetime.now(UTC))
            )
