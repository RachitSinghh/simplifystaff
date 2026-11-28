import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.deps import (
    get_current_company,
    get_current_employee,
    get_db,
    require_role,
)
from app.models import Employee
from app.models.enums import EmployeeRole
from app.schemas.employee import EmployeeCreate, EmployeeOut, EmployeeUpdate

router = APIRouter(prefix="/employees", tags=["employees"])

NOT_FOUND_MESSAGE = "Employee not found."
DUPLICATE_PHONE_MESSAGE = "That phone number is already registered."
FORBIDDEN_MESSAGE = "You don't have access to do that."

SELF_UPDATE_FIELDS = {"address", "emergency_contact_name", "emergency_contact_phone", "photo_url"}


def _generate_employee_code(db: Session, company_id: uuid.UUID) -> str:
    count = db.scalar(
        select(func.count()).select_from(Employee).where(Employee.company_id == company_id)
    )
    return f"EMP-{count + 1:04d}"


def _can_manage(actor: Employee, target_location_id: uuid.UUID | None) -> bool:
    if actor.role == EmployeeRole.owner:
        return True
    if actor.role == EmployeeRole.branch_manager:
        return actor.location_id == target_location_id
    return False


@router.get("", response_model=list[EmployeeOut])
def list_employees(
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> list[Employee]:
    query = select(Employee).where(Employee.company_id == company_id, Employee.is_active.is_(True))

    if actor.role == EmployeeRole.staff:
        query = query.where(Employee.id == actor.id)
    elif actor.role != EmployeeRole.owner:
        query = query.where(Employee.location_id == actor.location_id)

    return list(db.scalars(query))


@router.get("/{employee_id}", response_model=EmployeeOut)
def get_employee(
    employee_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> Employee:
    target = db.get(Employee, employee_id)
    if target is None or target.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    allowed = (
        actor.role == EmployeeRole.owner
        or actor.id == target.id
        or (actor.role != EmployeeRole.staff and actor.location_id == target.location_id)
    )
    if not allowed:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    return target


@router.post("", response_model=EmployeeOut, status_code=status.HTTP_201_CREATED)
def create_employee(
    payload: EmployeeCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
    db: Session = Depends(get_db),
) -> Employee:
    if not _can_manage(actor, payload.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    employee = Employee(
        company_id=company_id,
        employee_code=_generate_employee_code(db, company_id),
        **payload.model_dump(),
    )
    db.add(employee)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE_PHONE_MESSAGE) from None

    return employee


@router.patch("/{employee_id}", response_model=EmployeeOut)
def update_employee(
    employee_id: uuid.UUID,
    payload: EmployeeUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> Employee:
    target = db.get(Employee, employee_id)
    if target is None or target.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    updates = payload.model_dump(exclude_unset=True)

    if actor.id == target.id:
        if set(updates) - SELF_UPDATE_FIELDS:
            raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)
    elif not _can_manage(actor, target.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    for field, value in updates.items():
        setattr(target, field, value)

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, DUPLICATE_PHONE_MESSAGE) from None

    return target


@router.post("/{employee_id}/deactivate", response_model=EmployeeOut)
def deactivate_employee(
    employee_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
    db: Session = Depends(get_db),
) -> Employee:
    target = db.get(Employee, employee_id)
    if target is None or target.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    if not _can_manage(actor, target.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    target.is_active = False
    target.end_date = date.today()
    db.commit()
    return target
