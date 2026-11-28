from datetime import UTC, date, datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import hash_secret
from app.db.session import SessionLocal
from app.main import app
from app.models import Company, Employee, OtpCode, RefreshToken
from app.models.enums import EmployeeRole

client = TestClient(app)


@pytest.fixture
def seeded_employees():
    db = SessionLocal()
    company = Company(name="Auth Test Co", sector="restaurant")
    db.add(company)
    db.flush()

    active_employee = Employee(
        company_id=company.id,
        employee_code="EMP-AUTH-ACTIVE",
        first_name="Active",
        last_name="Employee",
        phone="+10000000020",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
    )
    inactive_employee = Employee(
        company_id=company.id,
        employee_code="EMP-AUTH-INACTIVE",
        first_name="Inactive",
        last_name="Employee",
        phone="+10000000021",
        role=EmployeeRole.staff,
        start_date=date(2026, 1, 1),
        is_active=False,
    )
    db.add_all([active_employee, inactive_employee])
    db.commit()

    yield {"active": active_employee, "inactive": inactive_employee}

    db.query(RefreshToken).filter(
        RefreshToken.employee_id.in_([active_employee.id, inactive_employee.id])
    ).delete(synchronize_session=False)
    db.query(OtpCode).filter(
        OtpCode.employee_id.in_([active_employee.id, inactive_employee.id])
    ).delete(synchronize_session=False)
    db.commit()
    db.delete(active_employee)
    db.delete(inactive_employee)
    db.commit()
    db.delete(company)
    db.commit()
    db.close()


def test_request_otp_stores_only_hashed_code(seeded_employees):
    phone = seeded_employees["active"].phone

    response = client.post("/api/v1/auth/otp/request", json={"phone": phone})

    assert response.status_code == 200
    code = response.json()["code"]
    assert code is not None

    db = SessionLocal()
    otp = db.scalars(
        select(OtpCode).where(OtpCode.employee_id == seeded_employees["active"].id)
    ).first()
    db.close()
    assert otp is not None
    assert otp.code_hash == hash_secret(code)
    assert otp.code_hash != code


def test_request_otp_blocks_inactive_employee(seeded_employees):
    phone = seeded_employees["inactive"].phone

    response = client.post("/api/v1/auth/otp/request", json={"phone": phone})

    assert response.status_code == 403
    assert response.json()["detail"] == "This account is no longer active. Contact your manager."

    db = SessionLocal()
    otp = db.scalars(
        select(OtpCode).where(OtpCode.employee_id == seeded_employees["inactive"].id)
    ).first()
    db.close()
    assert otp is None


def test_request_otp_unknown_phone_does_not_reveal_registration():
    response = client.post("/api/v1/auth/otp/request", json={"phone": "+19999999999"})

    assert response.status_code == 200
    assert response.json()["code"] is None


def test_verify_otp_succeeds_and_issues_tokens(seeded_employees):
    phone = seeded_employees["active"].phone
    code = client.post("/api/v1/auth/otp/request", json={"phone": phone}).json()["code"]

    response = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]


def test_verify_otp_rejects_wrong_code(seeded_employees):
    phone = seeded_employees["active"].phone
    client.post("/api/v1/auth/otp/request", json={"phone": phone})

    response = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": "000000"})

    assert response.status_code == 401
    assert response.json()["detail"] == "That code doesn't match. Check the code and try again."


def test_verify_otp_rejects_reused_code_with_same_generic_message(seeded_employees):
    phone = seeded_employees["active"].phone
    code = client.post("/api/v1/auth/otp/request", json={"phone": phone}).json()["code"]
    client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})

    response = client.post("/api/v1/auth/otp/verify", json={"phone": phone, "code": code})

    assert response.status_code == 401
    assert response.json()["detail"] == "That code doesn't match. Check the code and try again."


def test_verify_otp_rejects_expired_code_with_same_generic_message(seeded_employees):
    employee = seeded_employees["active"]
    code = "123456"
    db = SessionLocal()
    db.add(
        OtpCode(
            company_id=employee.company_id,
            employee_id=employee.id,
            code_hash=hash_secret(code),
            expires_at=datetime.now(UTC) - timedelta(minutes=1),
        )
    )
    db.commit()
    db.close()

    response = client.post(
        "/api/v1/auth/otp/verify", json={"phone": employee.phone, "code": code}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "That code doesn't match. Check the code and try again."
