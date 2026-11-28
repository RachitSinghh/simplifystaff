import uuid
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict

from app.models.enums import ShiftStatus


class ShiftCreate(BaseModel):
    location_id: uuid.UUID
    employee_id: uuid.UUID | None = None
    shift_date: date
    start_time: time
    end_time: time
    status: ShiftStatus = ShiftStatus.draft


class ShiftUpdate(BaseModel):
    employee_id: uuid.UUID | None = None
    shift_date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    status: ShiftStatus | None = None


class CopyLastWeekRequest(BaseModel):
    location_id: uuid.UUID
    week_start: date


class ShiftOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    location_id: uuid.UUID
    employee_id: uuid.UUID | None
    shift_date: date
    start_time: time
    end_time: time
    status: ShiftStatus
    created_by: uuid.UUID
    created_at: datetime
    has_conflict: bool
