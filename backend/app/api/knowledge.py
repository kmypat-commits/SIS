"""
FastAPI router for knowledge base CRUD: machines, fixtures, setup methods, tools.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List

from ..db.database import get_db
from ..db import crud

router = APIRouter(prefix="/api/knowledge", tags=["knowledge"])


# ── Machines ─────────────────────────────────────────────────────────────────

@router.get("/machines")
def list_machines(db: Session = Depends(get_db)):
    return [
        {
            "machine_id": m.machine_id,
            "machine_type": m.machine_type,
            "name": m.name,
            "capabilities": m.capabilities,
            "workspace_mm": m.workspace_mm,
            "accuracy": m.accuracy,
            "machine_minute_cost_kzt": m.machine_minute_cost_kzt,
            "coolant_supported": m.coolant_supported,
        }
        for m in crud.get_all_machines(db)
    ]

@router.post("/machines")
def upsert_machine(payload: Dict[str, Any], db: Session = Depends(get_db)):
    m = crud.upsert_machine(db, payload)
    return {"machine_id": m.machine_id, "status": "saved"}

@router.delete("/machines/{machine_id}")
def delete_machine(machine_id: str, db: Session = Depends(get_db)):
    ok = crud.delete_machine(db, machine_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Machine not found")
    return {"status": "deleted"}


# ── Fixtures ──────────────────────────────────────────────────────────────────

@router.get("/fixtures")
def list_fixtures(db: Session = Depends(get_db)):
    return [
        {
            "fixture_id": f.fixture_id,
            "fixture_type": f.fixture_type,
            "name": f.name,
            "compatible_machines": f.compatible_machines,
            "setup_time_min": f.setup_time_min,
            "setup_cost_kzt": f.setup_cost_kzt,
            "basing_options": f.basing_options,
        }
        for f in crud.get_all_fixtures(db)
    ]

@router.post("/fixtures")
def upsert_fixture(payload: Dict[str, Any], db: Session = Depends(get_db)):
    fx = crud.upsert_fixture(db, payload)
    return {"fixture_id": fx.fixture_id, "status": "saved"}

@router.delete("/fixtures/{fixture_id}")
def delete_fixture(fixture_id: str, db: Session = Depends(get_db)):
    ok = crud.delete_fixture(db, fixture_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Fixture not found")
    return {"status": "deleted"}


# ── Setup Methods ──────────────────────────────────────────────────────────────

@router.get("/setup-methods")
def list_setup_methods(db: Session = Depends(get_db)):
    return [
        {
            "setup_method_id": s.setup_method_id,
            "name": s.name,
            "time_min": s.time_min,
            "cost_kzt": s.cost_kzt,
            "setup_error_mm": s.setup_error_mm,
        }
        for s in crud.get_all_setup_methods(db)
    ]

@router.post("/setup-methods")
def upsert_setup_method(payload: Dict[str, Any], db: Session = Depends(get_db)):
    sm = crud.upsert_setup_method(db, payload)
    return {"setup_method_id": sm.setup_method_id, "status": "saved"}

@router.delete("/setup-methods/{mid}")
def delete_setup_method(mid: str, db: Session = Depends(get_db)):
    ok = crud.delete_setup_method(db, mid)
    if not ok:
        raise HTTPException(status_code=404, detail="Setup method not found")
    return {"status": "deleted"}


# ── Tools ─────────────────────────────────────────────────────────────────────

@router.get("/tools")
def list_tools(db: Session = Depends(get_db)):
    return [
        {
            "tool_id": t.tool_id,
            "tool_type": t.tool_type,
            "name": t.name,
            "diameter_mm": t.diameter_mm,
            "flutes": t.flutes,
            "coating": t.coating,
            "tool_cost_kzt": t.tool_cost_kzt,
            "tool_life_min": t.tool_life_min,
            "compatible_material_groups": t.compatible_material_groups,
            "cutting_data": t.cutting_data,
        }
        for t in crud.get_all_tools(db)
    ]

@router.post("/tools")
def upsert_tool(payload: Dict[str, Any], db: Session = Depends(get_db)):
    t = crud.upsert_tool(db, payload)
    return {"tool_id": t.tool_id, "status": "saved"}

@router.delete("/tools/{tool_id}")
def delete_tool(tool_id: str, db: Session = Depends(get_db)):
    ok = crud.delete_tool(db, tool_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Tool not found")
    return {"status": "deleted"}
