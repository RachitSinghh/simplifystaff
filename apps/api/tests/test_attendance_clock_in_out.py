from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import AttendanceRecord, Company, Employee, Location, Shift
from app.models.enums import EmployeeRole

client = TestClient(app)


@pytest.fixture
def branch_with_staff():
    db = SessionLocal()
    company = Company(name="Attendance Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    db.add(location)
    db.flush()

    staff = Employee(
        company_id=company.id,
        location_id=location.id,
        employee_code="EMP-ATT-STAFF",
        first_name="Staff",
        last_name="A",
        phone="+10000000110",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add(staff)
    db.commit()

    yield {"company": company, "location": location, "staff": staff}

    db.query(AttendanceRecord).filter(AttendanceRecord.employee_id == staff.id).delete(
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


def auth_headers(employee_id):
    return {"Authorization": f"Bearer {create_access_token(str(employee_id))}"}


def test_clock_in_with_no_scheduled_shift_succeeds_unscheduled(branch_with_staff):
    response = client.post(
        "/api/v1/attendance/clock-in", headers=auth_headers(branch_with_staff["staff"].id)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["shift_id"] is None
    assert body["status"] == "on_time"


def test_clock_in_shortly_after_shift_start_is_on_time(branch_with_staff):
    now = datetime.now(UTC)
    db = SessionLocal()
    shift = Shift(
        company_id=branch_with_staff["company"].id,
        location_id=branch_with_staff["location"].id,
        employee_id=branch_with_staff["staff"].id,
        shift_date=now.date(),
        start_time=(now - timedelta(minutes=2)).time(),
        end_time=(now + timedelta(hours=8)).time(),
        created_by=branch_with_staff["staff"].id,
    )
    db.add(shift)
    db.commit()
    db.close()

    response = client.post(
        "/api/v1/attendance/clock-in", headers=auth_headers(branch_with_staff["staff"].id)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "on_time"
    assert body["shift_id"] is not None


def test_clock_in_well_after_shift_start_is_late(branch_with_staff):
    now = datetime.now(UTC)
    db = SessionLocal()
    shift = Shift(
        company_id=branch_with_staff["company"].id,
        location_id=branch_with_staff["location"].id,
        employee_id=branch_with_staff["staff"].id,
        shift_date=now.date(),
        start_time=(now - timedelta(minutes=20)).time(),
        end_time=(now + timedelta(hours=8)).time(),
        created_by=branch_with_staff["staff"].id,
    )
    db.add(shift)
    db.commit()
    db.close()

    response = client.post(
        "/api/v1/attendance/clock-in", headers=auth_headers(branch_with_staff["staff"].id)
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "late"
    assert body["minutes_late"] >= 19


def test_clock_out_with_no_open_record_is_404(branch_with_staff):
    response = client.post(
        "/api/v1/attendance/clock-out", headers=auth_headers(branch_with_staff["staff"].id)
    )

    assert response.status_code == 404


def test_clock_out_closes_the_open_record(branch_with_staff):
    headers = auth_headers(branch_with_staff["staff"].id)
    client.post("/api/v1/attendance/clock-in", headers=headers)

    response = client.post("/api/v1/attendance/clock-out", headers=headers)

    assert response.status_code == 200
    assert response.json()["clock_out_at"] is not None
