from uuid import uuid4
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.session import get_db_session
from app.models.domain import Project
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


async def _get_project_or_404(project_id: str, db: AsyncSession) -> Project:
    project = await db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db_session),
):
    stmt = select(Project).order_by(Project.created_at.desc()).offset(skip).limit(limit)
    if status:
        stmt = stmt.where(Project.status == status)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db_session)):
    db_project = Project(project_id=str(uuid4()), **project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db_session)):
    return await _get_project_or_404(project_id, db)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session),
):
    db_project = await _get_project_or_404(project_id, db)
    for field, value in project.model_dump(exclude_unset=True).items():
        setattr(db_project, field, value)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db_session)):
    db_project = await _get_project_or_404(project_id, db)
    await db.delete(db_project)
    await db.commit()
    return {"message": "Project deleted"}
