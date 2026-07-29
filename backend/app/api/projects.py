"""
FastAPI router for project CRUD.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Any, Dict

from ..db.database import get_db
from ..db import crud

router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("/")
def list_projects(db: Session = Depends(get_db)):
    projects = crud.get_all_projects(db)
    return [
        {
            "project_id": p.project_id,
            "name": p.name,
            "production_type": p.production_type,
            "batch_size": p.batch_size,
            "material": p.material_name,
        }
        for p in projects
    ]


@router.get("/{project_id}")
def get_project(project_id: str, db: Session = Depends(get_db)):
    proj = crud.get_project(db, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    return {
        "project_id": proj.project_id,
        "name": proj.name,
        "currency": proj.currency,
        "production_type": proj.production_type,
        "batch_size": proj.batch_size,
        "material_name": proj.material_name,
        "material_group": proj.material_group,
        "hardness_hb": proj.hardness_hb,
        "product": proj.product_json,
        "strategy": proj.strategy_json,
        "resources": proj.resources_json,
        "process_templates": proj.process_templates_json,
        "costs": proj.costs_json,
        "quality_models": proj.quality_models_json,
    }


@router.post("/")
def create_or_update_project(payload: Dict[str, Any], db: Session = Depends(get_db)):
    proj_data = payload.get("project", payload)
    mat = proj_data.get("material", {})
    flat = {
        "project_id": proj_data.get("project_id", ""),
        "name": proj_data.get("name", ""),
        "currency": proj_data.get("currency", "KZT"),
        "production_type": proj_data.get("production_type", "serial"),
        "batch_size": proj_data.get("batch_size", 1),
        "material_name": mat.get("name", ""),
        "material_group": mat.get("group", "steel"),
        "hardness_hb": mat.get("hardness_hb", 0),
        "product_json": payload.get("product"),
        "strategy_json": payload.get("strategy"),
        "resources_json": payload.get("resources"),
        "process_templates_json": payload.get("process_templates"),
        "costs_json": payload.get("costs"),
        "quality_models_json": payload.get("quality_models"),
    }
    proj = crud.upsert_project(db, flat)
    return {"project_id": proj.project_id, "status": "saved"}


@router.delete("/{project_id}")
def delete_project(project_id: str, db: Session = Depends(get_db)):
    ok = crud.delete_project(db, project_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}
