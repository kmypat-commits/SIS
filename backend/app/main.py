"""
FastAPI application entry point for MachOpt-6L.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.database import engine
from .db.orm_models import Base
from .db.database import SessionLocal
from .db.seed import seed_if_empty
from .api import projects, knowledge, optimize, report

# Create tables
Base.metadata.create_all(bind=engine)

# Seed on startup
with SessionLocal() as db:
    seed_if_empty(db)

app = FastAPI(
    title="MachOpt-6L API",
    description="Система оптимизации технологических процессов механической обработки",
    version="1.0.0",
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


@app.get("/")
def root():
    return {
        "system": "MachOpt-6L",
        "version": "1.0.0",
        "description": "Система параметрической и структурной оптимизации ТП механической обработки",
        "docs": "/docs",
    }
