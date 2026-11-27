import uuid

from sqlalchemy import Enum, ForeignKey, text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.enums import KpiDirection


class Kpi(Base):
    __tablename__ = "kpis"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    company_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("companies.id"))
    name: Mapped[str]
    unit: Mapped[str]
    direction: Mapped[KpiDirection] = mapped_column(Enum(KpiDirection, native_enum=False, length=32))
    is_active: Mapped[bool] = mapped_column(server_default=text("true"))
