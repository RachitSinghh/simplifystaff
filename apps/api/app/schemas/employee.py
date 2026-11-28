import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict

from app.models.enums import EmployeeRole


class EmployeeCreate(BaseModel):
    first_name: str
    last_name: str
    phone: str
    role: EmployeeRole
    location_id: uuid.UUID | None = None
    job_title_id: uuid.UUID | None = None
    email: str | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    start_date: date


class EmployeeUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    phone: str | None = None
    email: str | None = None
    role: EmployeeRole | None = None
    location_id: uuid.UUID | None = None
    job_title_id: uuid.UUID | None = None
    address: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    photo_url: str | None = None
    start_date: date | None = None


class EmployeeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    employee_code: str
    first_name: str
    last_name: str
    phone: str
    email: str | None
    role: EmployeeRole
    location_id: uuid.UUID | None
    job_title_id: uuid.UUID | None
    address: str | None
    emergency_contact_name: str | None
    emergency_contact_phone: str | None
    photo_url: str | None
    start_date: date
    end_date: date | None
    is_active: bool
