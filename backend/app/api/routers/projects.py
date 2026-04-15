from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import uuid4
from typing import List
from sqlalchemy import text

from app.database.session import get_db_session
from app.schemas.projects import ProjectCreate, ProjectUpdate, ProjectResponse

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(db: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT * FROM projects ORDER BY created_at DESC")
    result = await db.execute(stmt)
    rows = result.fetchall()
    return [ProjectResponse(**dict(row)) for row in rows]


@router.post("/", response_model=ProjectResponse)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db_session)):
    project_id = str(uuid4())
    stmt = text("""
        INSERT INTO projects (project_id, project_name, customer, status, start_date, target_completion, memo, created_at, updated_at)
        VALUES (:project_id, :project_name, :customer, :status, :start_date, :target_completion, :memo, NOW(), NOW())
        RETURNING *
    """)
    result = await db.execute(stmt, {
        "project_id": project_id,
        "project_name": project.project_name,
        "customer": project.customer,
        "status": project.status.value if hasattr(project.status, 'value') else "IN_PROGRESS",
        "start_date": project.start_date,
        "target_completion": project.target_completion,
        "memo": project.memo,
    })
    row = result.fetchone()
    return ProjectResponse(**dict(row))


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("SELECT * FROM projects WHERE project_id = :project_id")
    result = await db.execute(stmt, {"project_id": project_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse(**dict(row))


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: str,
    project: ProjectUpdate,
    db: AsyncSession = Depends(get_db_session)
):
    stmt_check = text("SELECT * FROM projects WHERE project_id = :project_id")
    result = await db.execute(stmt_check, {"project_id": project_id})
    row = result.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Project not found")

    update_fields = []
    params = {"project_id": project_id}
    for field, value in project.model_dump(exclude_unset=True).items():
        if value is not None:
            update_fields.append(f"{field} = :{field}")
            params[field] = value.value if hasattr(value, 'value') else value

    if update_fields:
        stmt = text(f"""
            UPDATE projects
            SET {', '.join(update_fields)}, updated_at = NOW()
            WHERE project_id = :project_id
            RETURNING *
        """)
        result = await db.execute(stmt, params)
        row = result.fetchone()

    return ProjectResponse(**dict(row))


@router.delete("/{project_id}")
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db_session)):
    stmt = text("DELETE FROM projects WHERE project_id = :project_id")
    result = await db.execute(stmt, {"project_id": project_id})
    if result.rowcount == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    await db.commit()
    return {"message": "Project deleted"}
