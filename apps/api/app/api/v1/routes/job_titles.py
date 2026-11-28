import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_company, get_db, require_role
from app.models import Employee, JobTitle
from app.models.enums import EmployeeRole
from app.schemas.job_title import JobTitleIn, JobTitleOut, JobTitleUpdate

router = APIRouter(prefix="/job-titles", tags=["job-titles"])

NOT_FOUND_MESSAGE = "Job title not found."


@router.get("", response_model=list[JobTitleOut])
def list_job_titles(
    company_id: uuid.UUID = Depends(get_current_company),
    db: Session = Depends(get_db),
) -> list[JobTitle]:
    return list(db.scalars(select(JobTitle).where(JobTitle.company_id == company_id)))


@router.post("", response_model=JobTitleOut, status_code=status.HTTP_201_CREATED)
def create_job_title(
    payload: JobTitleIn,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner)),
    db: Session = Depends(get_db),
) -> JobTitle:
    job_title = JobTitle(company_id=company_id, name=payload.name)
    db.add(job_title)
    db.commit()
    return job_title


@router.patch("/{job_title_id}", response_model=JobTitleOut)
def update_job_title(
    job_title_id: uuid.UUID,
    payload: JobTitleUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner)),
    db: Session = Depends(get_db),
) -> JobTitle:
    job_title = db.get(JobTitle, job_title_id)
    if job_title is None or job_title.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(job_title, field, value)

    db.commit()
    return job_title
