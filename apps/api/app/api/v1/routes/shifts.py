import uuid
from datetime import date, timedelta

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
from app.models.enums import EmployeeRole, ShiftStatus
from app.schemas.shift import CopyLastWeekRequest, ShiftCreate, ShiftOut, ShiftUpdate

router = APIRouter(prefix="/shifts", tags=["shifts"])

NOT_FOUND_MESSAGE = "Shift not found."
FORBIDDEN_MESSAGE = "You don't have access to do that."
WEEK_ALREADY_HAS_SHIFTS_MESSAGE = "This week already has shifts. Clear them before copying."

READ_ROLES = (EmployeeRole.owner, EmployeeRole.branch_manager, EmployeeRole.shift_supervisor)


def _can_manage_location(actor: Employee, location_id: uuid.UUID) -> bool:
    if actor.role == EmployeeRole.owner:
        return True
    if actor.role == EmployeeRole.branch_manager:
        return actor.location_id == location_id
    return False


def _week_bounds(day: date) -> tuple[date, date]:
    week_start = day - timedelta(days=day.weekday())
    return week_start, week_start + timedelta(days=6)


def _shifts_overlap(a: Shift, b: Shift) -> bool:
    return a.shift_date == b.shift_date and a.start_time < b.end_time and b.start_time < a.end_time


def _has_conflict(db: Session, company_id: uuid.UUID, shift: Shift) -> bool:
    if shift.employee_id is None:
        return False

    week_start, week_end = _week_bounds(shift.shift_date)
    other_shifts = db.scalars(
        select(Shift).where(
            Shift.company_id == company_id,
            Shift.employee_id == shift.employee_id,
            Shift.id != shift.id,
            Shift.shift_date.between(week_start, week_end),
        )
    ).all()
    return any(_shifts_overlap(shift, other) for other in other_shifts)


def _serialize(db: Session, company_id: uuid.UUID, shift: Shift) -> ShiftOut:
    return ShiftOut(
        id=shift.id,
        location_id=shift.location_id,
        employee_id=shift.employee_id,
        shift_date=shift.shift_date,
        start_time=shift.start_time,
        end_time=shift.end_time,
        status=shift.status,
        created_by=shift.created_by,
        created_at=shift.created_at,
        has_conflict=_has_conflict(db, company_id, shift),
    )


@router.get("", response_model=list[ShiftOut])
def list_shifts(
    shift_date: date | None = Query(default=None),
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    actor: Employee = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> list[ShiftOut]:
    query = select(Shift).where(Shift.company_id == company_id)
    if location_ids is not None:
        query = query.where(Shift.location_id.in_(location_ids))
    if shift_date is not None:
        query = query.where(Shift.shift_date == shift_date)

    shifts = db.scalars(query).all()
    return [_serialize(db, company_id, shift) for shift in shifts]


@router.get("/{shift_id}", response_model=ShiftOut)
def get_shift(
    shift_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    actor: Employee = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> ShiftOut:
    shift = db.get(Shift, shift_id)
    if (
        shift is None
        or shift.company_id != company_id
        or (location_ids is not None and shift.location_id not in location_ids)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)
    return _serialize(db, company_id, shift)


@router.post("", response_model=ShiftOut, status_code=status.HTTP_201_CREATED)
def create_shift(
    payload: ShiftCreate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
    db: Session = Depends(get_db),
) -> ShiftOut:
    if not _can_manage_location(actor, payload.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    shift = Shift(company_id=company_id, created_by=actor.id, **payload.model_dump())
    db.add(shift)
    db.commit()
    return _serialize(db, company_id, shift)


@router.patch("/{shift_id}", response_model=ShiftOut)
def update_shift(
    shift_id: uuid.UUID,
    payload: ShiftUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
    db: Session = Depends(get_db),
) -> ShiftOut:
    shift = db.get(Shift, shift_id)
    if shift is None or shift.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    if not _can_manage_location(actor, shift.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(shift, field, value)

    db.commit()
    return _serialize(db, company_id, shift)


@router.post("/copy-last-week", response_model=list[ShiftOut], status_code=status.HTTP_201_CREATED)
def copy_last_week(
    payload: CopyLastWeekRequest,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
    db: Session = Depends(get_db),
) -> list[ShiftOut]:
    if not _can_manage_location(actor, payload.location_id):
        raise HTTPException(status.HTTP_403_FORBIDDEN, FORBIDDEN_MESSAGE)

    target_start = payload.week_start
    target_end = target_start + timedelta(days=6)
    source_start = target_start - timedelta(days=7)
    source_end = target_start - timedelta(days=1)

    target_week_has_shifts = db.scalar(
        select(Shift.id)
        .where(
            Shift.company_id == company_id,
            Shift.location_id == payload.location_id,
            Shift.shift_date.between(target_start, target_end),
        )
        .limit(1)
    )
    if target_week_has_shifts is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, WEEK_ALREADY_HAS_SHIFTS_MESSAGE)

    source_shifts = db.scalars(
        select(Shift).where(
            Shift.company_id == company_id,
            Shift.location_id == payload.location_id,
            Shift.shift_date.between(source_start, source_end),
        )
    ).all()

    copies = [
        Shift(
            company_id=company_id,
            location_id=payload.location_id,
            employee_id=shift.employee_id,
            shift_date=shift.shift_date + timedelta(days=7),
            start_time=shift.start_time,
            end_time=shift.end_time,
            status=ShiftStatus.draft,
            created_by=actor.id,
        )
        for shift in source_shifts
    ]
    db.add_all(copies)
    db.commit()
    return [_serialize(db, company_id, shift) for shift in copies]
