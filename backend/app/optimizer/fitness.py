"""
Fitness evaluator for MachOpt-6L.
Computes the 4 objective values for a Solution object.

Objectives (all minimize):
  1. time_total_min   – total machining + setup time
  2. cost_total_min   – total cost (machine rate + tool cost/part + fixture)
  3. setup_error_min  – worst setup error among operations
  4. quality_risk_min – composite quality risk score

Formulas/coefficients are kept simple and configurable via quality_models dict.
"""
from __future__ import annotations
import math
from typing import List, Dict, Any

from ..models.domain import Solution, OperationSolution, TransitionSolution


# ─── Time model ──────────────────────────────────────────────────────────────

def _basic_time_min(tr: TransitionSolution, op: OperationSolution) -> float:
    """
    Use pre-computed basic_time_min stored in transition solution.
    This is filled by the candidate generator.
    """
    return tr.basic_time_min


def _aux_time_fraction() -> float:
    """Auxiliary time = 20% of basic time (typical value for milling operations)."""
    return 0.20


# ─── Cost model ──────────────────────────────────────────────────────────────

def _tool_cost_per_part(tr: TransitionSolution, batch_size: int) -> float:
    """
    Tool cost allocated to one part = tool_cost_per_part_kzt (pre-computed
    in generator based on machining time / tool_life * tool_cost).
    """
    return tr.tool_cost_per_part_kzt


# ─── Quality risk model ──────────────────────────────────────────────────────

def _quality_risk(
    op: OperationSolution,
    transitions: List[TransitionSolution],
    weights: Dict[str, float],
) -> float:
    """
    Composite quality risk score (0..1 scale, normalized).
    risk = w1*setup_error + w2*machine_positioning + w3*cutting_aggressiveness
    """
    w_setup   = weights.get("setup_error_mm", 0.45)
    w_machine = weights.get("machine_positioning_mm", 0.35)
    w_cut     = weights.get("aggressive_cutting_penalty", 0.20)

    setup_err  = op.setup_error_mm          # mm
    mach_pos   = op.machine_positioning_mm  # mm

    # Aggressiveness: max fraction of upper cutting limit used (0..1)
    agg = 0.0
    if transitions:
        agg = max(
            getattr(tr, "_cutting_aggr", 0.5)
            for tr in transitions
        )

    # Normalize each component to [0..1] with rough reference values
    # setup_error reference: 0.10 mm is 1.0
    # machine_positioning reference: 0.025 mm is 1.0
    risk = (
        w_setup  * min(setup_err / 0.10, 1.0)
        + w_machine * min(mach_pos / 0.025, 1.0)
        + w_cut  * agg
    )
    return round(risk, 6)


# ─── Main evaluator ──────────────────────────────────────────────────────────

def evaluate(
    solution: Solution,
    quality_models: Dict[str, Any],
    batch_size: int = 1,
) -> Solution:
    """
    Fill solution.time_total_min, cost_total_min,
    setup_error_min, quality_risk_min in place and return solution.
    """
    qr_weights = (
        quality_models.get("quality_risk", {}).get("weights", {})
    )

    total_time = 0.0
    total_cost = 0.0
    max_setup_error = 0.0
    total_risk = 0.0
    op_count = 0

    for op in solution.operations:
        # Setup time & cost
        total_time += op.setup_time_min
        total_cost += op.setup_cost_kzt

        op_machine_cost = 0.0
        op_time_basic = 0.0
        for tr in op.transitions:
            bt = tr.basic_time_min
            aux = bt * _aux_time_fraction()
            op_time_basic += bt + aux
            op_machine_cost += (bt + aux) * op.machine_minute_cost_kzt
            total_cost += _tool_cost_per_part(tr, batch_size)

        total_time += op_time_basic
        total_cost += op_machine_cost

        # Setup error (worst case across operations)
        if op.setup_error_mm > max_setup_error:
            max_setup_error = op.setup_error_mm

        # Quality risk (average across operations)
        total_risk += _quality_risk(op, op.transitions, qr_weights)
        op_count += 1

    solution.time_total_min = round(total_time, 4)
    solution.cost_total_min = round(total_cost, 2)
    solution.setup_error_min = round(max_setup_error, 6)
    solution.quality_risk_min = round(total_risk / max(op_count, 1), 6)
    return solution


# ─── Pareto dominance check ───────────────────────────────────────────────────

def dominates(a: List[float], b: List[float]) -> bool:
    """Return True if solution-a dominates solution-b (all minimize)."""
    at_least_one_better = False
    for ai, bi in zip(a, b):
        if ai > bi:
            return False
        if ai < bi:
            at_least_one_better = True
    return at_least_one_better


def build_pareto_front(solutions: List[Solution]) -> List[Solution]:
    """Filter and return only non-dominated solutions."""
    pareto: List[Solution] = []
    for s in solutions:
        dominated = False
        to_remove = []
        sv = s.objectives_vector()
        for p in pareto:
            pv = p.objectives_vector()
            if dominates(pv, sv):
                dominated = True
                break
            if dominates(sv, pv):
                to_remove.append(p)
        if not dominated:
            for r in to_remove:
                pareto.remove(r)
            pareto.append(s)
    return pareto
