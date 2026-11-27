import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class Target(Base):
    __tablename__ = "targets"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"))
    employee_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"))
    kpi_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("kpis.id"))
    target_value: Mapped[Decimal]
    period_start: Mapped[date]
    period_end: Mapped[date]
    assigned_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
