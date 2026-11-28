from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, Location, Shift
from app.models.enums import EmployeeRole, ShiftStatus

client = TestClient(app)


@pytest.fixture
def branch_with_last_week_shifts():
    db = SessionLocal()
    company = Company(name="Copy Week Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    db.add(location)
    db.flush()

    manager = Employee(
        company_id=company.id,
        location_id=location.id,
        employee_code="EMP-CW-MGR",
        first_name="Manager",
        last_name="A",
        phone="+10000000090",
        role=EmployeeRole.branch_manager,
        start_date=date(2026, 1, 1),
    )
    staff = Employee(
        company_id=company.id,
        location_id=location.id,
        employee_code="EMP-CW-STAFF",
        first_name="Staff",
        last_name="A",
        phone="+10000000091",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add_all([manager, staff])
    db.commit()

    last_week_shift = Shift(
        company_id=company.id,
        location_id=location.id,
        employee_id=staff.id,
        shift_date=date(2026, 2, 2),
        start_time=time(9, 0),
        end_time=time(17, 0),
        status=ShiftStatus.published,
        created_by=manager.id,
    )
    db.add(last_week_shift)
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


def test_copy_last_week_creates_draft_shifts_for_new_week(branch_with_last_week_shifts):
    response = client.post(
        "/api/v1/shifts/copy-last-week",
        headers=auth_headers(branch_with_last_week_shifts["manager"].id),
        json={
            "location_id": str(branch_with_last_week_shifts["location"].id),
            "week_start": "2026-02-09",
        },
    )

    assert response.status_code == 201
    copies = response.json()
    assert len(copies) == 1
    assert copies[0]["shift_date"] == "2026-02-09"
    assert copies[0]["status"] == "draft"
    assert copies[0]["employee_id"] == str(branch_with_last_week_shifts["staff"].id)


def test_copy_last_week_twice_is_blocked_not_duplicated(branch_with_last_week_shifts):
    first = client.post(
        "/api/v1/shifts/copy-last-week",
        headers=auth_headers(branch_with_last_week_shifts["manager"].id),
        json={
            "location_id": str(branch_with_last_week_shifts["location"].id),
            "week_start": "2026-02-09",
        },
    )
    assert first.status_code == 201

    second = client.post(
        "/api/v1/shifts/copy-last-week",
        headers=auth_headers(branch_with_last_week_shifts["manager"].id),
        json={
            "location_id": str(branch_with_last_week_shifts["location"].id),
            "week_start": "2026-02-09",
        },
    )

    assert second.status_code == 409
