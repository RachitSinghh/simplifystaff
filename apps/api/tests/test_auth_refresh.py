from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from app.core.security import hash_secret
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, RefreshToken
from app.models.enums import EmployeeRole

client = TestClient(app)

SESSION_ENDED_MESSAGE = "Your session has ended. Log in again."


@pytest.fixture
def employee_with_refresh_token():
    db = SessionLocal()
    company = Company(name="Refresh Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    employee = Employee(
        company_id=company.id,
        employee_code="EMP-REFRESH-1",
        first_name="Refresh",
        last_name="Tester",
        phone="+10000000030",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    db.add(employee)
    db.flush()

    refresh_token_value = "plain-refresh-token-value"
    refresh_token = RefreshToken(
        company_id=company.id,
        employee_id=employee.id,
        token_hash=hash_secret(refresh_token_value),
        expires_at=datetime.now(UTC) + timedelta(days=30),
    )
    db.add(refresh_token)
    db.commit()

    yield employee, refresh_token_value

    db.query(RefreshToken).filter(RefreshToken.employee_id == employee.id).delete(
        synchronize_session=False
    )
    db.commit()
    db.delete(employee)
    db.commit()
    db.delete(company)
    db.commit()
    db.close()


def test_refresh_with_valid_token_issues_new_access_token(employee_with_refresh_token):
    _, refresh_token_value = employee_with_refresh_token

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_value})

    assert response.status_code == 200
    assert response.json()["access_token"]


def test_refresh_with_unknown_token_is_session_ended(employee_with_refresh_token):
    response = client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-real-token"})

    assert response.status_code == 401
    assert response.json()["detail"] == SESSION_ENDED_MESSAGE


def test_refresh_with_revoked_token_is_session_ended(employee_with_refresh_token):
    employee, refresh_token_value = employee_with_refresh_token
    db = SessionLocal()
    token = (
        db.query(RefreshToken)
        .filter(RefreshToken.employee_id == employee.id)
        .one()
    )
    token.revoked_at = datetime.now(UTC)
    db.commit()
    db.close()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_value})

    assert response.status_code == 401
    assert response.json()["detail"] == SESSION_ENDED_MESSAGE


def test_refresh_with_expired_token_is_session_ended(employee_with_refresh_token):
    employee, refresh_token_value = employee_with_refresh_token
    db = SessionLocal()
    token = (
        db.query(RefreshToken)
        .filter(RefreshToken.employee_id == employee.id)
        .one()
    )
    token.expires_at = datetime.now(UTC) - timedelta(minutes=1)
    db.commit()
    db.close()

    response = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token_value})

    assert response.status_code == 401
    assert response.json()["detail"] == SESSION_ENDED_MESSAGE


def test_logout_revokes_the_token(employee_with_refresh_token):
    employee, refresh_token_value = employee_with_refresh_token

    response = client.post("/api/v1/auth/logout", json={"refresh_token": refresh_token_value})
    assert response.status_code == 204

    db = SessionLocal()
    token = (
        db.query(RefreshToken)
        .filter(RefreshToken.employee_id == employee.id)
        .one()
    )
    db.close()
    assert token.revoked_at is not None


def test_deactivating_employee_revokes_all_their_refresh_tokens(employee_with_refresh_token):
    employee, _ = employee_with_refresh_token

    db = SessionLocal()
    target = db.get(Employee, employee.id)
    target.is_active = False
    db.commit()

    token = db.query(RefreshToken).filter(RefreshToken.employee_id == employee.id).one()
    assert token.revoked_at is not None
    db.close()
