import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import AttendanceStatus


class AttendanceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_id: uuid.UUID
    shift_id: uuid.UUID | None
    clock_in_at: datetime
    clock_out_at: datetime | None
    status: AttendanceStatus
    minutes_late: int
