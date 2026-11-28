from datetime import UTC, date, datetime, timedelta

import pytest

from app.db.session import SessionLocal
from app.models import AttendanceRecord, Company, Employee, Location, Shift
from app.models.enums import AttendanceStatus, EmployeeRole
from app.services.attendance_service import close_stale_open_records


@pytest.fixture
def branch_with_open_records():
    db = SessionLocal()
    company = Company(name="Close Stale Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    db.add(location)
    db.flush()

    staff = Employee(
        company_id=company.id,
        location_id=location.id,
        employee_code="EMP-CS-STAFF",
        first_name="Staff",
        last_name="A",
        phone="+10000000130",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add(staff)
    db.flush()

    now = datetime.now(UTC)

    ended_shift = Shift(
        company_id=company.id,
        location_id=location.id,
        employee_id=staff.id,
        shift_date=now.date(),
        start_time=(now - timedelta(hours=10)).time(),
        end_time=(now - timedelta(hours=2)).time(),
        created_by=staff.id,
    )
    ongoing_shift = Shift(
        company_id=company.id,
        location_id=location.id,
        employee_id=staff.id,
        shift_date=(now + timedelta(days=1)).date(),
        start_time=now.time(),
        end_time=(now + timedelta(hours=8)).time(),
        created_by=staff.id,
    )
    db.add_all([ended_shift, ongoing_shift])
    db.flush()

    past_shift_record = AttendanceRecord(
        company_id=company.id,
        employee_id=staff.id,
        shift_id=ended_shift.id,
        clock_in_at=now - timedelta(hours=10),
        clock_out_at=None,
        status=AttendanceStatus.on_time,
        minutes_late=0,
    )
    still_open_record = AttendanceRecord(
        company_id=company.id,
        employee_id=staff.id,
        shift_id=ongoing_shift.id,
        clock_in_at=now,
        clock_out_at=None,
        status=AttendanceStatus.on_time,
        minutes_late=0,
    )
    db.add_all([past_shift_record, still_open_record])
    db.commit()

    yield {
        "company": company,
        "past_shift_record": past_shift_record,
        "still_open_record": still_open_record,
    }

    db.query(AttendanceRecord).filter(AttendanceRecord.company_id == company.id).delete(
        synchronize_session=False
    )
    db.query(Shift).filter(Shift.company_id == company.id).delete(synchronize_session=False)
    db.commit()
    db.delete(staff)
    db.commit()
    db.delete(location)
    db.commit()
    db.delete(company)
    db.commit()
    db.close()


def test_close_stale_open_records_closes_past_shift_end_only(branch_with_open_records):
    db = SessionLocal()
    now = datetime.now(UTC)

    closed = close_stale_open_records(db, now)
    closed_ids = {record.id for record in closed}

    assert branch_with_open_records["past_shift_record"].id in closed_ids
    assert branch_with_open_records["still_open_record"].id not in closed_ids

    refreshed_past = db.get(AttendanceRecord, branch_with_open_records["past_shift_record"].id)
    refreshed_open = db.get(AttendanceRecord, branch_with_open_records["still_open_record"].id)
    assert refreshed_past.clock_out_at is not None
    assert refreshed_open.clock_out_at is None
    db.close()
