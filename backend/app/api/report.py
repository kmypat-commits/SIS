"""
Report API: GET /api/report/{project_id} → HTML
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse
from typing import Any, Dict

from .optimize import _results_cache, _solution_to_dict
from ..reports.generator import generate_html_report

router = APIRouter(prefix="/api/report", tags=["report"])


@router.get("/{project_id}", response_class=HTMLResponse)
def get_report(project_id: str):
    cache = _results_cache.get(project_id)
    if not cache:
        raise HTTPException(status_code=404, detail="No optimization results found")

    pareto_dicts = [_solution_to_dict(s) for s in cache["pareto"]]
    selected_dict = _solution_to_dict(cache["selected"]) if cache.get("selected") else ({} if not pareto_dicts else pareto_dicts[0])

    html = generate_html_report(
        project_name=project_id,
        selected=selected_dict,
        pareto=pareto_dicts,
        strategy_label="Парето-оптимизация",
    )
    return HTMLResponse(content=html)
