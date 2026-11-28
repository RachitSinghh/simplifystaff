from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, Location
from app.models.enums import EmployeeRole

client = TestClient(app)


@pytest.fixture
def two_branch_company():
    db = SessionLocal()
    company = Company(name="Locations Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    location_a = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    location_b = Location(company_id=company.id, name="Branch B", address="B St", timezone="UTC")
    db.add_all([location_a, location_b])
    db.flush()

    owner = Employee(
        company_id=company.id,
        employee_code="EMP-LOC-OWNER",
        first_name="Owner",
        last_name="O",
        phone="+10000000040",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    manager_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-LOC-MGR-A",
        first_name="Manager",
        last_name="A",
        phone="+10000000041",
        role=EmployeeRole.branch_manager,
        start_date=date(2026, 1, 1),
    )
    db.add_all([owner, manager_a])
    db.commit()

    yield {"company": company, "location_a": location_a, "location_b": location_b, "owner": owner, "manager_a": manager_a}

    db.delete(owner)
    db.delete(manager_a)
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


def test_owner_sees_both_branches(two_branch_company):
    response = client.get(
        "/api/v1/locations", headers=auth_headers(two_branch_company["owner"].id)
    )

    assert response.status_code == 200
    names = {row["name"] for row in response.json()}
    assert {"Branch A", "Branch B"} <= names


def test_manager_sees_only_own_branch(two_branch_company):
    response = client.get(
        "/api/v1/locations", headers=auth_headers(two_branch_company["manager_a"].id)
    )

    assert response.status_code == 200
    names = {row["name"] for row in response.json()}
    assert names == {"Branch A"}


def test_manager_cannot_get_another_branch(two_branch_company):
    response = client.get(
        f"/api/v1/locations/{two_branch_company['location_b'].id}",
        headers=auth_headers(two_branch_company["manager_a"].id),
    )

    assert response.status_code == 404


def test_owner_can_create_location(two_branch_company):
    response = client.post(
        "/api/v1/locations",
        headers=auth_headers(two_branch_company["owner"].id),
        json={"name": "Branch C", "address": "C St", "timezone": "UTC"},
    )

    assert response.status_code == 201
    created_id = response.json()["id"]

    db = SessionLocal()
    db.query(Location).filter(Location.id == created_id).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_manager_cannot_create_location(two_branch_company):
    response = client.post(
        "/api/v1/locations",
        headers=auth_headers(two_branch_company["manager_a"].id),
        json={"name": "Branch D", "address": "D St", "timezone": "UTC"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have access to do that."


def test_manager_cannot_update_location(two_branch_company):
    response = client.patch(
        f"/api/v1/locations/{two_branch_company['location_a'].id}",
        headers=auth_headers(two_branch_company["manager_a"].id),
        json={"name": "Renamed"},
    )

    assert response.status_code == 403
