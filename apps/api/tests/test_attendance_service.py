from datetime import UTC, datetime, timedelta

from app.models.enums import AttendanceStatus
from app.services.attendance_service import (
    GRACE_PERIOD_MINUTES,
    compute_clock_in_status,
)


def test_clock_in_before_grace_deadline_is_on_time():
    shift_start = datetime(2026, 2, 2, 9, 0, tzinfo=UTC)
    clock_in_at = shift_start + timedelta(minutes=GRACE_PERIOD_MINUTES - 1)

    status, minutes_late = compute_clock_in_status(clock_in_at, shift_start)

    assert status == AttendanceStatus.on_time
    assert minutes_late == 0


def test_clock_in_exactly_at_grace_deadline_is_on_time():
    shift_start = datetime(2026, 2, 2, 9, 0, tzinfo=UTC)
    clock_in_at = shift_start + timedelta(minutes=GRACE_PERIOD_MINUTES)

    status, minutes_late = compute_clock_in_status(clock_in_at, shift_start)

    assert status == AttendanceStatus.on_time
    assert minutes_late == 0


def test_clock_in_one_second_past_grace_deadline_is_late():
    shift_start = datetime(2026, 2, 2, 9, 0, tzinfo=UTC)
    clock_in_at = shift_start + timedelta(minutes=GRACE_PERIOD_MINUTES, seconds=1)

    status, minutes_late = compute_clock_in_status(clock_in_at, shift_start)

    assert status == AttendanceStatus.late
    assert minutes_late == GRACE_PERIOD_MINUTES
