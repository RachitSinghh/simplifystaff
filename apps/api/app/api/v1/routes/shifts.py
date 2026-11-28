import uuid
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    get_accessible_location_ids,
    get_current_company,
    get_db,
    require_role,
)
from app.models import Employee, Shift
from app.models.enums import EmployeeRole
from app.schemas.shift import ShiftCreate, ShiftOut, ShiftUpdate

router = APIRouter(prefix="/shifts", tags=["shifts"])

NOT_FOUND_MESSAGE = "Shift not found."
FORBIDDEN_MESSAGE = "You don't have access to do that."

READ_ROLES = (EmployeeRole.owner, EmployeeRole.branch_manager, EmployeeRole.shift_supervisor)


def _can_manage_location(actor: Employee, location_id: uuid.UUID) -> bool:
    if actor.role == EmployeeRole.owner:
        return True
    if actor.role == EmployeeRole.branch_manager:
        return actor.location_id == location_id
    return False


@router.get("", response_model=list[ShiftOut])
def list_shifts(
    shift_date: date | None = Query(default=None),
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    actor: Employee = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> list[Shift]:
    query = select(Shift).where(Shift.company_id == company_id)
    if location_ids is not None:
        query = query.where(Shift.location_id.in_(location_ids))
    if shift_date is not None:
        query = query.where(Shift.shift_date == shift_date)
    return list(db.scalars(query))


@router.get("/{shift_id}", response_model=ShiftOut)
def get_shift(
    shift_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    actor: Employee = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> Shift:
    shift = db.get(Shift, shift_id)
    if (
        shift is None
        or shift.company_id != company_id
        or (location_ids is not None and shift.location_id not in location_ids)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)
    return shift


@router.post("", response_model=ShiftOut, status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: ShiftCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
    db: Session = Depends(get_db),
) -> Shift:
    if not _can_manage_location(actor, payload.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    shift = Shift(company_id=company_id, created_by=actor.id, **payload.model_dump())
    db.add(shift)
    db.commit()
    return shift


@router.patch("/{shift_id}", response_model=ShiftOut)
def update_shift(
    shift_id: uuid.UUID,
    payload: ShiftUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
    db: Session = Depends(get_db),
) -> Shift:
    shift = db.get(Shift, shift_id)
    if shift is None or shift.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    if not _can_manage_location(actor, shift.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(shift, field, value)

    db.commit()
    return shift
