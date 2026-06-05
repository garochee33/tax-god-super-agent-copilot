"""Tax God API - Project Management Endpoints"""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DBSession
from app.models.project import Project

router = APIRouter()


class ProjectCreate(BaseModel):
    client_id: str | None = None
    name: str = Field(..., min_length=1, max_length=255)
    status: str = Field(default="active", max_length=50)
    budget: float | None = None
    spent: float = 0
    start_date: datetime | None = None
    end_date: datetime | None = None
    description: str | None = None


class ProjectUpdate(BaseModel):
    client_id: str | None = None
    name: str | None = Field(default=None, max_length=255)
    status: str | None = Field(default=None, max_length=50)
    budget: float | None = None
    spent: float | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    description: str | None = None


class ProjectResponse(BaseModel):
    id: str
    owner_id: str
    client_id: str | None
    name: str
    status: str
    budget: float | None
    spent: float
    start_date: datetime | None
    end_date: datetime | None
    description: str | None
    created_at: datetime
    updated_at: datetime


class ProjectListResponse(BaseModel):
    projects: list[ProjectResponse]
    total: int
    page: int
    per_page: int


@router.get("", response_model=ProjectListResponse)
async def list_projects(
    current_user: CurrentUser,
    db: DBSession,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
):
    query = select(Project).where(Project.owner_id == current_user.id)
    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()
    query = query.order_by(Project.updated_at.desc()).offset((page - 1) * per_page).limit(per_page)
    results = (await db.execute(query)).scalars().all()
    return ProjectListResponse(
        projects=[ProjectResponse.model_validate(p, from_attributes=True) for p in results],
        total=total,
        page=page,
        per_page=per_page,
    )


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(body: ProjectCreate, current_user: CurrentUser, db: DBSession):
    project = Project(owner_id=current_user.id, **body.model_dump())
    db.add(project)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: str, body: ProjectUpdate, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    await db.commit()
    await db.refresh(project)
    return ProjectResponse.model_validate(project, from_attributes=True)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(project_id: str, current_user: CurrentUser, db: DBSession):
    result = await db.execute(select(Project).where(Project.id == project_id, Project.owner_id == current_user.id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.delete(project)
    await db.commit()
