from datetime import UTC, date, datetime

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, Location, RefreshToken
from app.models.enums import EmployeeRole

client = TestClient(app)


@pytest.fixture
def two_branch_company():
    db = SessionLocal()
    company = Company(name="Employees Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location_a = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    location_b = Location(company_id=company.id, name="Branch B", address="B St", timezone="UTC")
    db.add_all([location_a, location_b])
    db.flush()

    owner = Employee(
        company_id=company.id,
        employee_code="EMP-EE-OWNER",
        first_name="Owner",
        last_name="O",
        phone="+10000000060",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    manager_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-EE-MGR-A",
        first_name="Manager",
        last_name="A",
        phone="+10000000061",
        role=EmployeeRole.branch_manager,
        start_date=date(2026, 1, 1),
    )
    staff_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-EE-STAFF-A",
        first_name="Staff",
        last_name="A",
        phone="+10000000062",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    staff_b = Employee(
        company_id=company.id,
        location_id=location_b.id,
        employee_code="EMP-EE-STAFF-B",
        first_name="Staff",
        last_name="B",
        phone="+10000000063",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add_all([owner, manager_a, staff_a, staff_b])
    db.commit()

    created_ids = []

    yield {
        "company": company,
        "location_a": location_a,
        "location_b": location_b,
        "owner": owner,
        "manager_a": manager_a,
        "staff_a": staff_a,
        "staff_b": staff_b,
        "created_ids": created_ids,
    }

    db.query(RefreshToken).filter(
        RefreshToken.employee_id.in_(
            [owner.id, manager_a.id, staff_a.id, staff_b.id, *created_ids]
        )
    ).delete(synchronize_session=False)
    db.query(Employee).filter(Employee.id.in_(created_ids)).delete(synchronize_session=False)
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


def test_create_assigns_auto_employee_code(two_branch_company):
    response = client.post(
        "/api/v1/employees",
        headers=auth_headers(two_branch_company["owner"].id),
        json={
            "first_name": "New",
            "last_name": "Hire",
            "phone": "+10000000070",
            "role": "staff",
            "location_id": str(two_branch_company["location_a"].id),
            "start_date": "2026-01-01",
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["employee_code"].startswith("EMP-")
    two_branch_company["created_ids"].append(body["id"])


def test_create_duplicate_phone_is_rejected(two_branch_company):
    response = client.post(
        "/api/v1/employees",
        headers=auth_headers(two_branch_company["owner"].id),
        json={
            "first_name": "Dup",
            "last_name": "Phone",
            "phone": two_branch_company["staff_a"].phone,
            "role": "staff",
            "location_id": str(two_branch_company["location_a"].id),
            "start_date": "2026-01-01",
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"] == "That phone number is already registered."


def test_manager_cannot_create_for_another_branch(two_branch_company):
    response = client.post(
        "/api/v1/employees",
        headers=auth_headers(two_branch_company["manager_a"].id),
        json={
            "first_name": "Cross",
            "last_name": "Branch",
            "phone": "+10000000071",
            "role": "staff",
            "location_id": str(two_branch_company["location_b"].id),
            "start_date": "2026-01-01",
        },
    )

    assert response.status_code == 403


def test_owner_lists_all_employees(two_branch_company):
    response = client.get(
        "/api/v1/employees", headers=auth_headers(two_branch_company["owner"].id)
    )

    assert response.status_code == 200
    codes = {row["employee_code"] for row in response.json()}
    assert {"EMP-EE-STAFF-A", "EMP-EE-STAFF-B"} <= codes


def test_manager_lists_only_own_branch(two_branch_company):
    response = client.get(
        "/api/v1/employees", headers=auth_headers(two_branch_company["manager_a"].id)
    )

    assert response.status_code == 200
    codes = {row["employee_code"] for row in response.json()}
    assert "EMP-EE-STAFF-A" in codes
    assert "EMP-EE-STAFF-B" not in codes


def test_staff_lists_only_self(two_branch_company):
    response = client.get(
        "/api/v1/employees", headers=auth_headers(two_branch_company["staff_a"].id)
    )

    assert response.status_code == 200
    codes = {row["employee_code"] for row in response.json()}
    assert codes == {"EMP-EE-STAFF-A"}


def test_staff_cannot_open_coworker_profile(two_branch_company):
    response = client.get(
        f"/api/v1/employees/{two_branch_company['staff_b'].id}",
        headers=auth_headers(two_branch_company["staff_a"].id),
    )

    assert response.status_code == 404


def test_staff_self_update_allows_contact_fields(two_branch_company):
    response = client.patch(
        f"/api/v1/employees/{two_branch_company['staff_a'].id}",
        headers=auth_headers(two_branch_company["staff_a"].id),
        json={"address": "New Address"},
    )

    assert response.status_code == 200
    assert response.json()["address"] == "New Address"


def test_staff_self_update_rejects_role_change(two_branch_company):
    response = client.patch(
        f"/api/v1/employees/{two_branch_company['staff_a'].id}",
        headers=auth_headers(two_branch_company["staff_a"].id),
        json={"role": "owner"},
    )

    assert response.status_code == 403


def test_deactivate_sets_inactive_and_end_date_and_revokes_sessions(two_branch_company):
    staff_a = two_branch_company["staff_a"]
    db = SessionLocal()
    db.add(
        RefreshToken(
            company_id=two_branch_company["company"].id,
            employee_id=staff_a.id,
            token_hash="irrelevant-for-this-test",
            expires_at=datetime(2099, 1, 1, tzinfo=UTC),
        )
    )
    db.commit()
    db.close()

    response = client.post(
        f"/api/v1/employees/{staff_a.id}/deactivate",
        headers=auth_headers(two_branch_company["manager_a"].id),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["is_active"] is False
    assert body["end_date"] is not None

    db = SessionLocal()
    token = db.query(RefreshToken).filter(RefreshToken.employee_id == staff_a.id).one()
    db.close()
    assert token.revoked_at is not None
