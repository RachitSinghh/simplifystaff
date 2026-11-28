import uuid
from datetime import date

import pytest
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.deps import SESSION_ENDED_MESSAGE, get_current_company, get_db
from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.models import Company, Employee
from app.models.enums import EmployeeRole

scoped_app = FastAPI()


@scoped_app.get("/scoped-employees")
def scoped_employees(company_id: uuid.UUID = Depends(get_current_company), db=Depends(get_db)):
    rows = db.scalars(select(Employee).where(Employee.company_id == company_id)).all()
    return [str(row.id) for row in rows]


client = TestClient(scoped_app)


@pytest.fixture
def two_companies():
    db = SessionLocal()
    company_a = Company(name="Company A", sector="restaurant")
    company_b = Company(name="Company B", sector="restaurant")
    db.add_all([company_a, company_b])
    db.flush()

    employee_a = Employee(
        company_id=company_a.id,
        employee_code="EMP-A001",
        first_name="Alice",
        last_name="A",
        phone="+10000000001",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    employee_b = Employee(
        company_id=company_b.id,
        employee_code="EMP-B001",
        first_name="Bob",
        last_name="B",
        phone="+10000000002",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    db.add_all([employee_a, employee_b])
    db.commit()

    yield employee_a, employee_b

    db.delete(employee_a)
    db.delete(employee_b)
    db.commit()
    db.delete(company_a)
    db.delete(company_b)
    db.commit()
    db.close()


def test_get_current_company_scopes_to_caller_company(two_companies):
    employee_a, employee_b = two_companies
    token = create_access_token(str(employee_a.id))

    response = client.get("/scoped-employees", headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 200
    ids = response.json()
    assert str(employee_a.id) in ids
    assert str(employee_b.id) not in ids


def test_missing_token_is_rejected():
    response = client.get("/scoped-employees")
    assert response.status_code in (401, 403)


def test_garbage_token_is_rejected():
    response = client.get("/scoped-employees", headers={"Authorization": "Bearer not-a-real-token"})
    assert response.status_code == 401
    assert response.json()["detail"] == SESSION_ENDED_MESSAGE
