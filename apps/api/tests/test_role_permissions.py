import uuid
from datetime import date

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.deps import (
    FORBIDDEN_MESSAGE,
    get_accessible_location_ids,
    get_current_company,
    get_db,
    require_role,
)
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models import Company, Employee, Location
from app.models.enums import EmployeeRole

permissions_app = FastAPI()


@permissions_app.get("/manager-only")
def manager_only(
    employee: Employee = Depends(require_role(EmployeeRole.owner, EmployeeRole.branch_manager)),
):
    return {"employee_id": str(employee.id)}


@permissions_app.get("/scoped-employees")
def scoped_employees(
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    db=Depends(get_db),
):
    query = select(Employee).where(Employee.company_id == company_id)
    if location_ids is not None:
        query = query.where(Employee.location_id.in_(location_ids))
    rows = db.scalars(query).all()
    return [str(row.id) for row in rows]


client = TestClient(permissions_app)


@pytest.fixture
def two_branch_company():
    db = SessionLocal()
    company = Company(name="Two Branch Co", sector="restaurant")
    db.add(company)
    db.flush()

    location_a = Location(company_id=company.id, name="Branch A", address="A St", timezone="UTC")
    location_b = Location(company_id=company.id, name="Branch B", address="B St", timezone="UTC")
    db.add_all([location_a, location_b])
    db.flush()

    owner = Employee(
        company_id=company.id,
        employee_code="EMP-OWNER",
        first_name="Owner",
        last_name="O",
        phone="+10000000010",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    manager_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-MGR-A",
        first_name="Manager",
        last_name="A",
        phone="+10000000011",
        role=EmployeeRole.branch_manager,
        start_date=date(2026, 1, 1),
    )
    staff_a = Employee(
        company_id=company.id,
        location_id=location_a.id,
        employee_code="EMP-STAFF-A",
        first_name="Staff",
        last_name="A",
        phone="+10000000012",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    staff_b = Employee(
        company_id=company.id,
        location_id=location_b.id,
        employee_code="EMP-STAFF-B",
        first_name="Staff",
        last_name="B",
        phone="+10000000013",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add_all([owner, manager_a, staff_a, staff_b])
    db.commit()

    yield {"owner": owner, "manager_a": manager_a, "staff_a": staff_a, "staff_b": staff_b}

    db.delete(owner)
    db.delete(manager_a)
    db.delete(staff_a)
    db.delete(staff_b)
    db.commit()
    db.delete(location_a)
    db.delete(location_b)
    db.commit()
    db.delete(company)
    db.commit()
    db.close()


def test_staff_cannot_call_manager_only_route(two_branch_company):
    token = create_access_token(str(two_branch_company["staff_a"].id))

    response = client.get("/manager-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 403
    assert response.json()["detail"] == FORBIDDEN_MESSAGE


def test_manager_can_call_manager_only_route(two_branch_company):
    token = create_access_token(str(two_branch_company["manager_a"].id))

    response = client.get("/manager-only", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200


def test_branch_manager_is_boxed_to_own_branch(two_branch_company):
    token = create_access_token(str(two_branch_company["manager_a"].id))

    response = client.get("/scoped-employees", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    ids = response.json()
    assert str(two_branch_company["staff_a"].id) in ids
    assert str(two_branch_company["staff_b"].id) not in ids


def test_owner_sees_both_branches(two_branch_company):
    token = create_access_token(str(two_branch_company["owner"].id))

    response = client.get("/scoped-employees", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    ids = response.json()
    assert str(two_branch_company["staff_a"].id) in ids
    assert str(two_branch_company["staff_b"].id) in ids
