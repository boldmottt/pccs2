from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.session import dispose_engine, get_engine
from app.models.domain import Base
from app.api.routers import projects, patterns, rounds, samples, inks, match, predict, import_rdp, bases, plates, rdp_data

settings = get_settings()


def _apply_light_migrations(sync_conn) -> None:
    """create_all은 기존 테이블에 새 컬럼을 추가하지 못하므로,
    개발용(알렘빅 없는) DB를 위해 누락 컬럼만 ALTER로 보충한다."""
    from sqlalchemy import inspect, text

    inspector = inspect(sync_conn)
    if "inks" in inspector.get_table_names():
        columns = {col["name"] for col in inspector.get_columns("inks")}
        if "plate_id" not in columns:
            sync_conn.execute(text("ALTER TABLE inks ADD COLUMN plate_id VARCHAR"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    engine = get_engine()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_apply_light_migrations)
    yield
    await dispose_engine()


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(bases.router)
app.include_router(patterns.router)
app.include_router(rounds.router)
app.include_router(samples.router)
app.include_router(inks.router)
app.include_router(match.router)
app.include_router(predict.router)
app.include_router(import_rdp.router)
app.include_router(plates.router)
app.include_router(rdp_data.router)


@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} v{settings.APP_VERSION}"}
