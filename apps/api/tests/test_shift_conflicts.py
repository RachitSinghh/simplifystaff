from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, Location, Shift
from app.models.enums import EmployeeRole

client = TestClient(app)


@pytest.fixture
def branch_with_staff():
    db = SessionLocal()
    company = Company(name="Conflicts Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    db.add(location)
    db.flush()

    manager = Employee(
        company_id=company.id,
        location_id=location.id,
        employee_code="EMP-CF-MGR",
        first_name="Manager",
        last_name="A",
        phone="+10000000100",
        role=EmployeeRole.branch_manager,
        start_date=date(2026, 1, 1),
    )
    staff = Employee(
        company_id=company.id,
        location_id=location.id,
        employee_code="EMP-CF-STAFF",
        first_name="Staff",
        last_name="A",
        phone="+10000000101",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add_all([manager, staff])
    db.commit()

    yield {"company": company, "location": location, "manager": manager, "staff": staff}

    db.query(Shift).filter(Shift.company_id == company.id).delete(synchronize_session=False)
    db.commit()
    db.delete(manager)
    db.delete(staff)
    db.commit()
    db.delete(location)
    db.commit()
    db.delete(company)
    db.commit()
    db.close()


def auth_headers(employee_id):
    return {"Authorization": f"Bearer {create_access_token(str(employee_id))}"}


def test_overlapping_shifts_flagged_but_both_saved(branch_with_staff):
    location = branch_with_staff["location"]
    staff = branch_with_staff["staff"]
    headers = auth_headers(branch_with_staff["manager"].id)

    first = client.post(
        "/api/v1/shifts",
        headers=headers,
        json={
            "location_id": str(location.id),
            "employee_id": str(staff.id),
            "shift_date": "2026-02-02",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    ).json()

    second = client.post(
        "/api/v1/shifts",
        headers=headers,
        json={
            "location_id": str(location.id),
            "employee_id": str(staff.id),
            "shift_date": "2026-02-02",
            "start_time": "15:00:00",
            "end_time": "23:00:00",
        },
    ).json()

    assert second is not None
    assert second["has_conflict"] is True

    list_response = client.get("/api/v1/shifts", headers=headers, params={"shift_date": "2026-02-02"})
    rows = {row["id"]: row for row in list_response.json()}
    assert rows[first["id"]]["has_conflict"] is True
    assert rows[second["id"]]["has_conflict"] is True


def test_non_overlapping_shifts_in_same_week_not_flagged(branch_with_staff):
    location = branch_with_staff["location"]
    staff = branch_with_staff["staff"]
    headers = auth_headers(branch_with_staff["manager"].id)

    monday = client.post(
        "/api/v1/shifts",
        headers=headers,
        json={
            "location_id": str(location.id),
            "employee_id": str(staff.id),
            "shift_date": "2026-02-02",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    ).json()

    tuesday = client.post(
        "/api/v1/shifts",
        headers=headers,
        json={
            "location_id": str(location.id),
            "employee_id": str(staff.id),
            "shift_date": "2026-02-03",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    ).json()

    assert monday["has_conflict"] is False
    assert tuesday["has_conflict"] is False
