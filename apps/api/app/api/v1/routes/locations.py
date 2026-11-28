import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import (
    get_accessible_location_ids,
    get_current_company,
    get_db,
    require_role,
)
from app.models import Employee, Location
from app.models.enums import EmployeeRole
from app.schemas.location import LocationIn, LocationOut, LocationUpdate

router = APIRouter(prefix="/locations", tags=["locations"])

NOT_FOUND_MESSAGE = "Location not found."


@router.get("", response_model=list[LocationOut])
def list_locations(
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    db: Session = Depends(get_db),
) -> list[Location]:
    query = select(Location).where(Location.company_id == company_id)
    if location_ids is not None:
        query = query.where(Location.id.in_(location_ids))
    return list(db.scalars(query))


@router.get("/{location_id}", response_model=LocationOut)
def get_location(
    location_id: uuid.UUID,
    company_id: uuid.UUID = Depends(get_current_company),
    location_ids: list[uuid.UUID] | None = Depends(get_accessible_location_ids),
    db: Session = Depends(get_db),
) -> Location:
    location = db.get(Location, location_id)
    if (
        location is None
        or location.company_id != company_id
        or (location_ids is not None and location.id not in location_ids)
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)
    return location


@router.post("", response_model=LocationOut, status_code=status.HTTP_201_CREATED)
def create_location(
    payload: LocationIn,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner)),
    db: Session = Depends(get_db),
) -> Location:
    location = Location(company_id=company_id, **payload.model_dump())
    db.add(location)
    db.commit()
    return location


@router.patch("/{location_id}", response_model=LocationOut)
def update_location(
    location_id: uuid.UUID,
    payload: LocationUpdate,
    company_id: uuid.UUID = Depends(get_current_company),
    actor: Employee = Depends(require_role(EmployeeRole.owner)),
    db: Session = Depends(get_db),
) -> Location:
    location = db.get(Location, location_id)
    if location is None or location.company_id != company_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NOT_FOUND_MESSAGE)

    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(location, field, value)

    db.commit()
    return location
