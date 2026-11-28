from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AttendanceRecord, Location, Shift
from app.models.enums import AttendanceStatus

GRACE_PERIOD_MINUTES = 10


def compute_clock_in_status(
    clock_in_at: datetime, shift_start_at: datetime
) -> tuple[AttendanceStatus, int]:
    deadline = shift_start_at + timedelta(minutes=GRACE_PERIOD_MINUTES)
    if clock_in_at <= deadline:
        return AttendanceStatus.on_time, 0

    minutes_late = int((clock_in_at - shift_start_at).total_seconds() // 60)
    return AttendanceStatus.late, minutes_late


def shift_start_at(shift: Shift, tz: ZoneInfo) -> datetime:
    return datetime.combine(shift.shift_date, shift.start_time, tzinfo=tz)


def shift_end_at(shift: Shift, tz: ZoneInfo) -> datetime:
    return datetime.combine(shift.shift_date, shift.end_time, tzinfo=tz)


def close_stale_open_records(db: Session, as_of: datetime) -> list[AttendanceRecord]:
    open_records = db.scalars(
        select(AttendanceRecord).where(AttendanceRecord.clock_out_at.is_(None))
    ).all()

    closed = []
    for record in open_records:
        shift = db.get(Shift, record.shift_id) if record.shift_id else None

        if shift is not None:
            location = db.get(Location, shift.location_id)
            tz = ZoneInfo(location.timezone) if location else UTC
            cutoff = shift_end_at(shift, tz)
        else:
            cutoff = datetime.combine(record.clock_in_at.date(), time(23, 59, 59), tzinfo=UTC)

        if as_of >= cutoff:
            record.clock_out_at = cutoff
            closed.append(record)

    db.commit()
    return closed


def today_in_timezone(reference: datetime, tz: ZoneInfo) -> date:
    return reference.astimezone(tz).date()
