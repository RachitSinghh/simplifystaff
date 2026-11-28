import uuid
from datetime import UTC, date, datetime
from zoneinfo import ZoneInfo

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.deps import (
    get_accessible_location_ids,
    get_current_company,
    get_current_employee,
    get_db,
    require_role,
)
from app.models import AttendanceRecord, Employee, Location, Shift
from app.models.enums import AttendanceStatus, EmployeeRole
from app.schemas.attendance import AttendanceOut
from app.services.attendance_service import (
    compute_clock_in_status,
    shift_start_at,
    today_in_timezone,
)

router = APIRouter(prefix="/attendance", tags=["attendance"])

NO_OPEN_RECORD_MESSAGE = "No open clock-in found to close."

READ_ROLES = (EmployeeRole.owner, EmployeeRole.branch_manager, EmployeeRole.shift_supervisor)


@router.post("/clock-in", response_model=AttendanceOut, status_code=status.HTTP_201_CREATED)
def clock_in(
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> AttendanceRecord:
    now = datetime.now(UTC)

    location = db.get(Location, actor.location_id) if actor.location_id else None
    tz = ZoneInfo(location.timezone) if location else UTC
    today_local = today_in_timezone(now, tz)

    shift = db.scalars(
        select(Shift).where(
            Shift.company_id == company_id,
            Shift.employee_id == actor.id,
            Shift.shift_date == today_local,
        )
    ).first()

    if shift is None:
        record = AttendanceRecord(
            company_id=company_id,
            employee_id=actor.id,
            shift_id=None,
            clock_in_at=now,
            status=AttendanceStatus.on_time,
            minutes_late=0,
        )
    else:
        attendance_status, minutes_late = compute_clock_in_status(now, shift_start_at(shift, tz))
        record = AttendanceRecord(
            company_id=company_id,
            employee_id=actor.id,
            shift_id=shift.id,
            clock_in_at=now,
            status=attendance_status,
            minutes_late=minutes_late,
        )

    db.add(record)
    db.commit()
    return record


@router.post("/clock-out", response_model=AttendanceOut)
def clock_out(
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(get_current_employee),
    db: Session = Depends(get_db),
) -> AttendanceRecord:
    record = db.scalars(
        select(AttendanceRecord)
        .where(
            AttendanceRecord.company_id == company_id,
            AttendanceRecord.employee_id == actor.id,
            AttendanceRecord.clock_out_at.is_(None),
        )
        .order_by(AttendanceRecord.clock_in_at.desc())
    ).first()

    if record is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_OPEN_RECORD_MESSAGE)

    record.clock_out_at = datetime.now(UTC)
    db.commit()
    return record


@router.get("", response_model=list[AttendanceOut])
def list_attendance(
    attendance_date: date | None = Query(default=None),
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    actor: Employee = Depends(require_role(*READ_ROLES)),
    db: Session = Depends(get_db),
) -> list[AttendanceRecord]:
    query = (
        select(AttendanceRecord)
        .join(Employee, AttendanceRecord.employee_id == Employee.id)
        .where(AttendanceRecord.company_id == company_id)
    )
    if location_ids is not None:
        query = query.where(Employee.location_id.in_(location_ids))
    if attendance_date is not None:
        query = query.where(func.date(AttendanceRecord.clock_in_at) == attendance_date)

    return list(db.scalars(query))
