"""
Post-Pareto strategy selector.
Given a Pareto front, applies a selection strategy to pick one "best" solution.
"""
from __future__ import annotations
from typing import List, Dict, Optional

from ..models.domain import Solution


OBJ_INDEX = {
    "time_total_min": 0,
    "cost_total_min": 1,
    "setup_error_min": 2,
    "quality_risk_min": 3,
}


def select_min_criterion(
    pareto: List[Solution],
    objective_id: str,
) -> Optional[Solution]:
    """Pick solution with the lowest value of the given objective."""
    if not pareto:
        return None
    key_map = {
        "time_total_min": lambda s: s.time_total_min,
        "cost_total_min": lambda s: s.cost_total_min,
        "setup_error_min": lambda s: s.setup_error_min,
        "quality_risk_min": lambda s: s.quality_risk_min,
    }
    fn = key_map.get(objective_id)
    if not fn:
        return pareto[0]
    return min(pareto, key=fn)


def select_weighted_sum(
    pareto: List[Solution],
    weights: Dict[str, float],
) -> Optional[Solution]:
    """
    Pick solution minimising Σ w_i * obj_i.
    weights keys: time_total_min, cost_total_min, setup_error_min, quality_risk_min.
    Normalises each objective to [0,1] before applying weights.
    """
    if not pareto:
        return None

    # Collect vectors
    vecs = [s.objectives_vector() for s in pareto]
    n_obj = len(vecs[0])

    # Normalize
    mins = [min(v[i] for v in vecs) for i in range(n_obj)]
    maxs = [max(v[i] for v in vecs) for i in range(n_obj)]

    obj_keys = ["time_total_min", "cost_total_min", "setup_error_min", "quality_risk_min"]
    w = [weights.get(k, 0.25) for k in obj_keys]

    best_sol = None
    best_score = float("inf")
    for sol, vec in zip(pareto, vecs):
        score = 0.0
        for i in range(n_obj):
            rng = maxs[i] - mins[i]
            norm = (vec[i] - mins[i]) / rng if rng > 1e-12 else 0.0
            score += w[i] * norm
        if score < best_score:
            best_score = score
            best_sol = sol
    return best_sol


def select_constraint_then_first(
    pareto: List[Solution],
    constraints: Dict,
) -> Optional[Solution]:
    """
    Filter front by hard constraints, then return first (lowest time).
    constraints keys:
      - max_setup_error_mm: float
      - max_quality_risk: float
      - max_cost_kzt: float
    """
    if not pareto:
        return None
    filtered = list(pareto)
    if "max_setup_error_mm" in constraints:
        filtered = [s for s in filtered if s.setup_error_min <= constraints["max_setup_error_mm"]]
    if "max_quality_risk" in constraints:
        filtered = [s for s in filtered if s.quality_risk_min <= constraints["max_quality_risk"]]
    if "max_cost_kzt" in constraints:
        filtered = [s for s in filtered if s.cost_total_min <= constraints["max_cost_kzt"]]
    if not filtered:
        return pareto[0]
    return min(filtered, key=lambda s: s.time_total_min)
