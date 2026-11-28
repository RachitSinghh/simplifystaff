from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import AttendanceRecord, Company, Employee, Location
from app.models.enums import AttendanceStatus, EmployeeRole

client = TestClient(app)


@pytest.fixture
def two_branch_company_with_attendance():
    db = SessionLocal()
    company = Company(name="Attendance List Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location_a = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    location_b = Location(company_id=company.id, name="Branch B", address="B St", timezone="UTC")
    db.add_all([location_a, location_b])
    db.flush()

    owner = Employee(
        company_id=company.id,
        employee_code="EMP-AL-OWNER",
        first_name="Owner",
        last_name="O",
        phone="+10000000120",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    manager_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-AL-MGR-A",
        first_name="Manager",
        last_name="A",
        phone="+10000000121",
        role=EmployeeRole.branch_manager,
        start_date=date(2026, 1, 1),
    )
    staff_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-AL-STAFF-A",
        first_name="Staff",
        last_name="A",
        phone="+10000000122",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    staff_b = Employee(
        company_id=company.id,
        location_id=location_b.id,
        employee_code="EMP-AL-STAFF-B",
        first_name="Staff",
        last_name="B",
        phone="+10000000123",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add_all([owner, manager_a, staff_a, staff_b])
    db.commit()

    now = datetime.now(UTC)
    record_a = AttendanceRecord(
        company_id=company.id,
        employee_id=staff_a.id,
        shift_id=None,
        clock_in_at=now,
        status=AttendanceStatus.on_time,
        minutes_late=0,
    )
    record_b = AttendanceRecord(
        company_id=company.id,
        employee_id=staff_b.id,
        shift_id=None,
        clock_in_at=now,
        status=AttendanceStatus.on_time,
        minutes_late=0,
    )
    db.add_all([record_a, record_b])
    db.commit()

    yield {
        "company": company,
        "owner": owner,
        "manager_a": manager_a,
        "staff_a": staff_a,
        "staff_b": staff_b,
    }

    db.query(AttendanceRecord).filter(AttendanceRecord.company_id == company.id).delete(
        synchronize_session=False
    )
    db.commit()
    db.delete(owner)
    db.delete(manager_a)
    db.delete(staff_a)
    db.delete(staff_b)
    db.commit()
    db.query(Location).filter(Location.id.in_([location_a.id, location_b.id])).delete(
        synchronize_session=False
    )
    db.commit()
    db.delete(company)
    db.commit()
    db.close()


def auth_headers(employee_id):
    return {"Authorization": f"Bearer {create_access_token(str(employee_id))}"}


def test_owner_sees_attendance_for_both_branches(two_branch_company_with_attendance):
    response = client.get(
        "/api/v1/attendance",
        headers=auth_headers(two_branch_company_with_attendance["owner"].id),
    )

    assert response.status_code == 200
    employee_ids = {row["employee_id"] for row in response.json()}
    assert str(two_branch_company_with_attendance["staff_a"].id) in employee_ids
    assert str(two_branch_company_with_attendance["staff_b"].id) in employee_ids


def test_manager_sees_only_own_branch_attendance(two_branch_company_with_attendance):
    response = client.get(
        "/api/v1/attendance",
        headers=auth_headers(two_branch_company_with_attendance["manager_a"].id),
    )

    assert response.status_code == 200
    employee_ids = {row["employee_id"] for row in response.json()}
    assert str(two_branch_company_with_attendance["staff_a"].id) in employee_ids
    assert str(two_branch_company_with_attendance["staff_b"].id) not in employee_ids


def test_unscheduled_record_with_null_shift_id_does_not_crash(two_branch_company_with_attendance):
    response = client.get(
        "/api/v1/attendance",
        headers=auth_headers(two_branch_company_with_attendance["owner"].id),
    )

    assert response.status_code == 200
    assert all(row["shift_id"] is None for row in response.json())
