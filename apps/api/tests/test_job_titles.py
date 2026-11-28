from datetime import date

import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, JobTitle
from app.models.enums import EmployeeRole

client = TestClient(app)


@pytest.fixture
def company_with_employees():
    db = SessionLocal()
    company = Company(name="Job Titles Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    owner = Employee(
        company_id=company.id,
        employee_code="EMP-JT-OWNER",
        first_name="Owner",
        last_name="O",
        phone="+10000000050",
        role=EmployeeRole.owner,
        start_date=date(2026, 1, 1),
    )
    staff = Employee(
        company_id=company.id,
        employee_code="EMP-JT-STAFF",
        first_name="Staff",
        last_name="S",
        phone="+10000000051",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add_all([owner, staff])
    db.commit()

    yield {"company": company, "owner": owner, "staff": staff}

    db.delete(owner)
    db.delete(staff)
    db.commit()
    db.delete(company)
    db.commit()
    db.close()


def auth_headers(employee_id):
    return {"Authorization": f"Bearer {create_access_token(str(employee_id))}"}


def test_owner_can_create_job_title(company_with_employees):
    response = client.post(
        "/api/v1/job-titles",
        headers=auth_headers(company_with_employees["owner"].id),
        json={"name": "Waiter"},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Waiter"
    assert body["is_active"] is True

    db = SessionLocal()
    db.query(JobTitle).filter(JobTitle.id == body["id"]).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_staff_cannot_create_job_title(company_with_employees):
    response = client.post(
        "/api/v1/job-titles",
        headers=auth_headers(company_with_employees["staff"].id),
        json={"name": "Chef"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "You don't have access to do that."


def test_staff_can_list_job_titles(company_with_employees):
    db = SessionLocal()
    job_title = JobTitle(company_id=company_with_employees["company"].id, name="Cashier")
    db.add(job_title)
    db.commit()
    job_title_id = job_title.id
    db.close()

    response = client.get(
        "/api/v1/job-titles", headers=auth_headers(company_with_employees["staff"].id)
    )

    assert response.status_code == 200
    assert any(row["name"] == "Cashier" for row in response.json())

    db = SessionLocal()
    db.query(JobTitle).filter(JobTitle.id == job_title_id).delete(synchronize_session=False)
    db.commit()
    db.close()


def test_owner_can_retire_job_title(company_with_employees):
    db = SessionLocal()
    job_title = JobTitle(company_id=company_with_employees["company"].id, name="Kitchen Helper")
    db.add(job_title)
    db.commit()
    job_title_id = job_title.id
    db.close()

    response = client.patch(
        f"/api/v1/job-titles/{job_title_id}",
        headers=auth_headers(company_with_employees["owner"].id),
        json={"is_active": False},
    )

    assert response.status_code == 200
    assert response.json()["is_active"] is False

    db = SessionLocal()
    db.query(JobTitle).filter(JobTitle.id == job_title_id).delete(synchronize_session=False)
    db.commit()
    db.close()
