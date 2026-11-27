import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class KpiProgressEntry(Base):
    __tablename__ = "kpi_progress_entries"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"))
    target_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("targets.id"))
    value: Mapped[Decimal]
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    recorded_by: Mapped[uuid.UUID] = mapped_column(ForeignKey("employees.id"))
