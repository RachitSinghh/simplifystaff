import uuid
from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import decode_access_token
from app.db.session import SessionLocal
from app.models import Employee
from app.models.enums import EmployeeRole

bearer_scheme = HTTPBearer()

SESSION_ENDED_MESSAGE = "Your session has ended. Log in again."
FORBIDDEN_MESSAGE = "You don't have access to do that."


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_employee(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Employee:
    employee_id = decode_access_token(credentials.credentials)
    try:
        employee = db.get(Employee, uuid.UUID(employee_id)) if employee_id else None
    except ValueError:
        employee = None

    if employee is None or not employee.is_active:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, SESSION_ENDED_MESSAGE)

    return employee


def get_current_company(employee: Employee = Depends(get_current_employee)) -> uuid.UUID:
    return employee.company_id


def require_role(*roles: EmployeeRole):
    def checker(employee: Employee = Depends(get_current_employee)) -> Employee:
        if employee.role not in roles:
            raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)
        return employee

    return checker


def get_accessible_location_ids(
    employee: Employee = Depends(get_current_employee),
) -> list[uuid.UUID] | None:
    if employee.role == EmployeeRole.owner:
        return None
    return [employee.location_id] if employee.location_id else []
