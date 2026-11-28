from fastapi import APIRouter

from app.api.v1.routes import attendance, auth, employees, job_titles, locations, shifts

api_router = APIRouter()
api_router.include_router(auth.router)
api_router.include_router(employees.router)
api_router.include_router(locations.router)
api_router.include_router(job_titles.router)
api_router.include_router(shifts.router)
api_router.include_router(attendance.router)
