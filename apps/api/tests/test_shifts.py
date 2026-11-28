from datetime import date, time

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, Location, Shift
from app.models.enums import EmployeeRole

client = TestClient(app)


@pytest.fixture
def two_branch_company():
    db = SessionLocal()
    company = Company(name="Shifts Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location_a = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    location_b = Location(company_id=company.id, name="Branch B", address="B St", timezone="UTC")
    db.add_all([location_a, location_b])
    db.flush()

    owner = Employee(
        company_id=company.id,
        employee_code="EMP-SH-OWNER",
        first_name="Owner",
        last_name="O",
        phone="+10000000080",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    manager_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-SH-MGR-A",
        first_name="Manager",
        last_name="A",
        phone="+10000000081",
        role=EmployeeRole.branch_manager,
        start_date=date(2026, 1, 1),
    )
    supervisor_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-SH-SUP-A",
        first_name="Supervisor",
        last_name="A",
        phone="+10000000082",
        role=EmployeeRole.shift_supervisor,
        start_date=date(2026, 1, 1),
    )
    staff_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-SH-STAFF-A",
        first_name="Staff",
        last_name="A",
        phone="+10000000083",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add_all([owner, manager_a, supervisor_a, staff_a])
    db.commit()

    shift_a = Shift(
        company_id=company.id,
        location_id=location_a.id,
        employee_id=staff_a.id,
        shift_date=date(2026, 2, 1),
        start_time=time(9, 0),
        end_time=time(17, 0),
        created_by=manager_a.id,
    )
    shift_b = Shift(
        company_id=company.id,
        location_id=location_b.id,
        employee_id=None,
        shift_date=date(2026, 2, 1),
        start_time=time(9, 0),
        end_time=time(17, 0),
        created_by=owner.id,
    )
    db.add_all([shift_a, shift_b])
    db.commit()

    yield {
        "company": company,
        "location_a": location_a,
        "location_b": location_b,
        "owner": owner,
        "manager_a": manager_a,
        "supervisor_a": supervisor_a,
        "staff_a": staff_a,
        "shift_a": shift_a,
        "shift_b": shift_b,
    }

    db.query(Shift).filter(Shift.company_id == company.id).delete(synchronize_session=False)
    db.commit()
    db.delete(owner)
    db.delete(manager_a)
    db.delete(supervisor_a)
    db.delete(staff_a)
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


def test_manager_lists_only_own_branch_shifts(two_branch_company):
    response = client.get(
        "/api/v1/shifts", headers=auth_headers(two_branch_company["manager_a"].id)
    )

    assert response.status_code == 200
    location_ids = {row["location_id"] for row in response.json()}
    assert location_ids == {str(two_branch_company["location_a"].id)}


def test_manager_cannot_create_shift_for_another_branch(two_branch_company):
    response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(two_branch_company["manager_a"].id),
        json={
            "location_id": str(two_branch_company["location_b"].id),
            "shift_date": "2026-02-02",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    )

    assert response.status_code == 403


def test_manager_creates_open_slot_shift_with_null_employee(two_branch_company):
    response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(two_branch_company["manager_a"].id),
        json={
            "location_id": str(two_branch_company["location_a"].id),
            "shift_date": "2026-02-02",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["employee_id"] is None
    assert body["status"] == "draft"

    db = SessionLocal()
    db.query(Shift).filter(Shift.id == body["id"]).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_supervisor_can_list_but_not_create(two_branch_company):
    list_response = client.get(
        "/api/v1/shifts", headers=auth_headers(two_branch_company["supervisor_a"].id)
    )
    assert list_response.status_code == 200

    create_response = client.post(
        "/api/v1/shifts",
        headers=auth_headers(two_branch_company["supervisor_a"].id),
        json={
            "location_id": str(two_branch_company["location_a"].id),
            "shift_date": "2026-02-02",
            "start_time": "09:00:00",
            "end_time": "17:00:00",
        },
    )
    assert create_response.status_code == 403


def test_supervisor_cannot_update_shift(two_branch_company):
    response = client.patch(
        f"/api/v1/shifts/{two_branch_company['shift_a'].id}",
        headers=auth_headers(two_branch_company["supervisor_a"].id),
        json={"status": "published"},
    )

    assert response.status_code == 403


def test_owner_sees_both_branches_and_can_update_any(two_branch_company):
    list_response = client.get(
        "/api/v1/shifts", headers=auth_headers(two_branch_company["owner"].id)
    )
    assert list_response.status_code == 200
    location_ids = {row["location_id"] for row in list_response.json()}
    assert location_ids == {
        str(two_branch_company["location_a"].id),
        str(two_branch_company["location_b"].id),
    }

    update_response = client.patch(
        f"/api/v1/shifts/{two_branch_company['shift_b'].id}",
        headers=auth_headers(two_branch_company["owner"].id),
        json={"status": "published"},
    )
    assert update_response.status_code == 200
    assert update_response.json()["status"] == "published"
