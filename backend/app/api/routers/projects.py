from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4

from app.database.session import get_db_session
from app.models.domain import Project, ProjectStatus
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=list[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db_session)):
    """Get all projects ordered by created_at descending"""
    result = await db.execute(
        select(Project).order_by(Project.created_at.desc())
    )
    projects = result.scalars().all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db_session)):
    """Create a new project"""
    project_id = str(uuid4())

    db_project = Project(
        project_id=project_id,
        project_name=project.project_name,
        customer=project.customer,
        status=ProjectStatus.IN_PROGRESS.value,
        start_date=project.start_date,
        target_completion=project.target_completion,
        memo=project.memo,
    )

    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)

    return ProjectResponse.model_validate(db_project)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db_session)):
    """Get a specific project by ID"""
    result = await db.execute(select(Project).where(Project.project_id == project_id))
    project = result.scalar_one_or_none()

    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    """Update an existing project"""
    result = await db.execute(
        select(Project).where(Project.project_id == project_id)
    )
    db_project = result.scalar_one_or_none()

    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update only provided fields
    update_data = project.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(db_project, field, value)

    await db.commit()
    await db.refresh(db_project)

    return ProjectResponse.model_validate(db_project)


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db_session)):
    """Delete a project by ID"""
    result = await db.execute(
        select(Project).where(Project.project_id == project_id)
    )
    db_project = result.scalar_one_or_none()

    if not db_project:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(db_project)
    await db.commit()

    return {"message": "Project deleted"}
