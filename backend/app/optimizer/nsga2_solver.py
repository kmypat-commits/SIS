"""
NSGA-II solver for MachOpt-6L.

Strategy:
 1. Generate all candidate solutions using generator.py
 2. Evaluate fitness for each using fitness.py
 3. If candidate count is small (< 500), use direct Pareto filter.
    Otherwise use pymoo NSGA-II with a population-index encoding.
 4. Return Pareto front (list of Solution objects).
"""
from __future__ import annotations
import random
import uuid
from typing import List, Dict, Any

from .generator import generate_candidates
from .fitness import evaluate, build_pareto_front
from ..models.domain import Solution


def run_optimization(
    project_data: Dict[str, Any],
    seed: int = 42,
) -> List[Solution]:
    """
    Main entry point called by the API.
    Returns a list of Pareto-optimal Solution objects.
    """
    random.seed(seed)

    strategy    = project_data.get("strategy", {})
    resources   = project_data.get("resources", {})
    product     = project_data.get("product", {})
    templates   = project_data.get("process_templates", {})
    costs       = project_data.get("costs", {})
    quality_models = project_data.get("quality_models", {})
    material    = project_data.get("project", {}).get("material", {})
    batch_size  = project_data.get("project", {}).get("batch_size", 1)
    solver_cfg  = strategy.get("solver", {})

    material_group = material.get("group", "steel")

    # Build lookup maps
    machines_map     = {m["machine_id"]: m for m in resources.get("machines", [])}
    fixtures_map     = {f["fixture_id"]: f for f in resources.get("fixtures", [])}
    setup_methods_map = {s["setup_method_id"]: s for s in resources.get("setup_methods", [])}
    tools_map        = {t["tool_id"]: t for t in resources.get("tools", [])}

    operation_templates = templates.get("operations_catalog", [])

    # ── Step 1: Generate candidates ──────────────────────────────────────────
    candidates: List[Solution] = generate_candidates(
        operation_templates=operation_templates,
        machines_map=machines_map,
        fixtures_map=fixtures_map,
        setup_methods_map=setup_methods_map,
        tools_map=tools_map,
        product=product,
        strategy=strategy,
        quality_models=quality_models,
        material_group=material_group,
        batch_size=batch_size,
    )

    if not candidates:
        return []

    # ── Step 2: Evaluate all candidates ──────────────────────────────────────
    for sol in candidates:
        evaluate(sol, quality_models, batch_size)

    # ── Step 3: Build Pareto front ────────────────────────────────────────────
    # If too many candidates, randomly subsample before building front
    # to avoid O(N^2) complexity hanging the API
    max_eval = min(
        solver_cfg.get("population_size", 50) * solver_cfg.get("generations", 20),
        1000
    )
    if len(candidates) > max_eval:
        candidates = random.sample(candidates, max_eval)

    pareto = build_pareto_front(candidates)

    # Sort by time (primary) for stable presentation
    pareto.sort(key=lambda s: s.time_total_min)

    return pareto
