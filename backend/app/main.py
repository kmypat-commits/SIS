from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse

from .db.database import engine
from .db.orm_models import Base
from .db.database import SessionLocal
from .db.seed import seed_if_empty
from .api import projects, knowledge, optimize, report


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        seed_if_empty(db)
    yield


app = FastAPI(
    title="MachOpt-6L API",
    description="Система оптимизации технологических процессов механической обработки",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(projects.router)
app.include_router(knowledge.router)
app.include_router(optimize.router)
app.include_router(report.router)

frontend_dir = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"
has_frontend = frontend_dir.is_dir()


@app.get("/")
async def root():
    if has_frontend:
        index = frontend_dir / "index.html"
        return HTMLResponse(index.read_text(encoding="utf-8"))
    return {
        "system": "MachOpt-6L",
        "version": "1.0.0",
        "description": "Система параметрической и структурной оптимизации ТП механической обработки",
        "docs": "/docs",
    }


@app.get("/{full_path:path}")
async def spa_catch(full_path: str):
    if full_path.startswith("api/"):
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    if not has_frontend:
        return JSONResponse({"detail": "Not Found"}, status_code=404)
    file_path = frontend_dir / full_path
    if file_path.is_file():
        return FileResponse(file_path)
    index = frontend_dir / "index.html"
    return HTMLResponse(index.read_text(encoding="utf-8"))
