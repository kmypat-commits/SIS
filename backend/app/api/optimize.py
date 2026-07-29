"""
FastAPI router for optimization: run solver, store results, retrieve Pareto front.
Results are stored in-memory (dict) for MVP simplicity.
"""
from __future__ import annotations
import json
import dataclasses
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Any, Dict, List, Optional

from ..db.database import get_db
from ..db import crud
from ..optimizer.nsga2_solver import run_optimization
from ..strategy.selector import (
    select_min_criterion,
    select_weighted_sum,
    select_constraint_then_first,
)
from ..models.domain import Solution

router = APIRouter(prefix="/api/optimize", tags=["optimize"])

# In-memory cache: project_id → {"pareto": [...], "selected": Solution | None}
_results_cache: Dict[str, Dict] = {}


def _solution_to_dict(sol: Solution) -> Dict:
    """Convert Solution dataclass to JSON-serializable dict."""
    ops = []
    for op in sol.operations:
        trs = []
        for tr in op.transitions:
            trs.append({
                "transition_id": tr.transition_id,
                "method": tr.method,
                "tool_id": tr.tool_id,
                "V": tr.V,
                "f": tr.f,
                "ap": tr.ap,
                "basic_time_min": tr.basic_time_min,
                "tool_cost_per_part_kzt": tr.tool_cost_per_part_kzt,
                "achieved_ra_um": tr.achieved_ra_um,
            })
        ops.append({
            "operation_id": op.operation_id,
            "name": op.name,
            "machine_id": op.machine_id,
            "fixture_id": op.fixture_id,
            "setup_method_id": op.setup_method_id,
            "setup_time_min": op.setup_time_min,
            "setup_cost_kzt": op.setup_cost_kzt,
            "setup_error_mm": op.setup_error_mm,
            "machine_positioning_mm": op.machine_positioning_mm,
            "machine_minute_cost_kzt": op.machine_minute_cost_kzt,
            "transitions": trs,
        })
    return {
        "solution_id": sol.solution_id,
        "operations": ops,
        "objectives": {
            "time_total_min": sol.time_total_min,
            "cost_total_min": sol.cost_total_min,
            "setup_error_min": sol.setup_error_min,
            "quality_risk_min": sol.quality_risk_min,
        },
    }


@router.post("/run/{project_id}")
def run_optimize(project_id: str, db: Session = Depends(get_db)):
    """Run optimization for a saved project. Returns the Pareto front."""
    proj = crud.get_project(db, project_id)
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")

    # Reconstruct full project dict
    project_data = {
        "project": {
            "project_id": proj.project_id,
            "name": proj.name,
            "currency": proj.currency,
            "production_type": proj.production_type,
            "batch_size": proj.batch_size,
            "material": {
                "name": proj.material_name,
                "group": proj.material_group,
                "hardness_hb": proj.hardness_hb,
            },
        },
        "strategy": proj.strategy_json or {},
        "product": proj.product_json or {},
        "resources": proj.resources_json or {},
        "process_templates": proj.process_templates_json or {},
        "costs": proj.costs_json or {},
        "quality_models": proj.quality_models_json or {},
    }

    seed = (project_data.get("strategy") or {}).get("solver", {}).get("seed", 42)
    pareto: List[Solution] = run_optimization(project_data, seed=seed)

    _results_cache[project_id] = {
        "pareto": pareto,
        "selected": None,
    }

    return {
        "project_id": project_id,
        "pareto_count": len(pareto),
        "pareto": [_solution_to_dict(s) for s in pareto],
    }


@router.get("/results/{project_id}")
def get_results(project_id: str):
    """Return cached Pareto results for a project."""
    cache = _results_cache.get(project_id)
    if not cache:
        raise HTTPException(status_code=404, detail="No results found. Run optimization first.")
    return {
        "pareto_count": len(cache["pareto"]),
        "pareto": [_solution_to_dict(s) for s in cache["pareto"]],
        "selected": _solution_to_dict(cache["selected"]) if cache["selected"] else None,
    }


@router.post("/select/{project_id}")
def select_solution(project_id: str, payload: Dict[str, Any]):
    """
    Select one solution from the Pareto front.
    payload: { "strategy": "min_criterion"|"weighted_sum"|"constraint_then_first",
               "objective_id": "...",          # for min_criterion
               "weights": {...},               # for weighted_sum
               "constraints": {...}            # for constraint_then_first
             }
    """
    cache = _results_cache.get(project_id)
    if not cache or not cache["pareto"]:
        raise HTTPException(status_code=404, detail="No Pareto results available")

    pareto = cache["pareto"]
    strategy = payload.get("strategy", "min_criterion")

    if strategy == "min_criterion":
        selected = select_min_criterion(pareto, payload.get("objective_id", "time_total_min"))
    elif strategy == "weighted_sum":
        selected = select_weighted_sum(pareto, payload.get("weights", {}))
    elif strategy == "constraint_then_first":
        selected = select_constraint_then_first(pareto, payload.get("constraints", {}))
    else:
        selected = pareto[0]

    cache["selected"] = selected
    return _solution_to_dict(selected) if selected else {}


@router.get("/export/{project_id}")
def export_json(project_id: str):
    """Export the selected solution as JSON."""
    cache = _results_cache.get(project_id)
    if not cache or not cache.get("selected"):
        raise HTTPException(status_code=404, detail="No selected solution")
    return _solution_to_dict(cache["selected"])
