"""
Candidate solution generator.
Enumerates all feasible combinations of:
  (machine, fixture, setup_method, tool, V, f, ap)
for each operation template, applying applicability rules.

For MVP, cutting parameter space is sampled at 3 levels each (low/mid/high).
"""
from __future__ import annotations
import math
import uuid
from itertools import product as itertools_product
from typing import List, Dict, Any, Tuple, Optional

from ..models.domain import (
    Solution, OperationSolution, TransitionSolution,
    Machine, Fixture, SetupMethod, Tool, CuttingData
)


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _sample_range(lo: float, hi: float, levels: int = 3) -> List[float]:
    """Return `levels` evenly-spaced values in [lo, hi]."""
    if levels == 1 or lo >= hi:
        return [(lo + hi) / 2]
    step = (hi - lo) / (levels - 1)
    return [round(lo + i * step, 4) for i in range(levels)]


def _map_method_to_capability(method: str) -> str:
    """Map transition method to machine capability tag."""
    mapping = {
        "face_milling_rough": "face_milling",
        "face_milling_finish": "face_milling",
        "pocket_rough": "pocket_milling",
        "pocket_finish": "pocket_milling",
        "spot_drill": "spot_drill",
        "drill": "drilling",
        "drill_core": "drilling",
        "ream_optional": "drilling",
        "tap": "tapping",
        "chamfer_milling": "chamfer",
    }
    return mapping.get(method, method)


def _roughness_for_method(method: str, quality_models: Dict) -> float:
    defaults = (
        quality_models
        .get("roughness_estimation", {})
        .get("defaults", {})
    )
    return defaults.get(method, {}).get("ra_um", 6.3)


def _basic_time(method: str, geometry: Dict, V: float, f: float, ap: float) -> float:
    """
    Simplified basic machining time (minutes) by method.
    Uses empirical formulas based on geometry/cutting data.
    """
    eps = 1e-9

    if "milling" in method or method in ("pocket_rough", "pocket_finish", "chamfer_milling"):
        # Face / pocket milling: L / (f * n)  where n = V*1000 / (pi*D)
        # Use a representative path length from geometry
        area = geometry.get("area_mm2", 0) or (
            geometry.get("length_mm", 100) * geometry.get("width_mm", 100)
        )
        tool_d = geometry.get("_tool_d", 63.0)
        n_rpm = (V * 1000) / (math.pi * tool_d + eps)
        passes = max(1, math.ceil(geometry.get("depth_mm", 2.0) / (ap + eps)))
        path_per_pass = math.sqrt(area) * 1.2  # rough path estimate
        t = (path_per_pass * passes) / (f * n_rpm + eps)
        return round(max(t, 0.5), 3)

    if method in ("drill", "drill_core", "spot_drill"):
        depth = geometry.get("depth_mm", 22.0)
        holes = len(geometry.get("holes", [{"hole_id": "H1"}]))
        tool_d = geometry.get("_tool_d", 8.5)
        n_rpm = (V * 1000) / (math.pi * tool_d + eps)
        t_per_hole = depth / (f * n_rpm + eps)
        return round(t_per_hole * holes, 3)

    if method == "tap":
        depth = geometry.get("depth_mm", 18.0)
        pitch = geometry.get("pitch_mm", 1.5)
        tool_d = geometry.get("_tool_d", 10.0)
        n_rpm = (V * 1000) / (math.pi * tool_d + eps)
        t = depth / (pitch * n_rpm + eps)
        return round(max(t * 2, 0.2), 3)  # *2 for reverse pass

    # Fallback
    return 1.0


# ─── Main generator ──────────────────────────────────────────────────────────

CUTTING_LEVELS = 3   # Low / Mid / High for V, f, ap


def generate_candidates(
    operation_templates: List[Dict],
    machines_map: Dict[str, Dict],
    fixtures_map: Dict[str, Dict],
    setup_methods_map: Dict[str, Dict],
    tools_map: Dict[str, Dict],
    product: Dict,
    strategy: Dict,
    quality_models: Dict,
    material_group: str = "steel",
    batch_size: int = 1,
) -> List[Solution]:
    """
    Generate all feasible Solution objects (one operation per template).
    Each Solution is a complete process plan.

    Returns a list of Solution objects with partially-filled objectives
    (objectives are computed later by fitness.evaluate).
    """
    allowed_machines = set(
        strategy.get("constraints", {}).get("allowed_machines", list(machines_map.keys()))
    )
    require_coolant = strategy.get("constraints", {}).get("require_coolant", False)

    # Build CDE geometry lookup keyed by cde_id
    cde_geom: Dict[str, Dict] = {}
    for cde in product.get("cde_list", []):
        cde_geom[cde["cde_id"]] = cde.get("geometry", {})

    # For each operation template, build a list of (machine, fixture, setup_method, [transitions]) options
    per_op_options: List[List[OperationSolution]] = []

    for op_tmpl in operation_templates:
        op_id = op_tmpl["operation_id"]
        op_name = op_tmpl["name"]
        applicable_cde = op_tmpl.get("applicable_cde", [])

        # Aggregate geometry from all applicable CDEs
        agg_geom: Dict = {}
        for cde_id in applicable_cde:
            g = cde_geom.get(cde_id, {})
            agg_geom.update(g)

        op_options: List[OperationSolution] = []

        for machine_id in op_tmpl.get("candidate_machines", []):
            if machine_id not in allowed_machines:
                continue
            machine = machines_map.get(machine_id)
            if not machine:
                continue
            if require_coolant and not machine.get("coolant_supported", False):
                continue

            for fixture_id in op_tmpl.get("candidate_fixtures", []):
                fixture = fixtures_map.get(fixture_id)
                if not fixture:
                    continue
                if machine_id not in fixture.get("compatible_machines", []):
                    continue

                for sm_id in op_tmpl.get("candidate_setup_methods", []):
                    sm = setup_methods_map.get(sm_id)
                    if not sm:
                        continue

                    # Build transition solutions for each transition template
                    op_transition_combos = _build_transition_combos(
                        op_tmpl.get("transitions", []),
                        tools_map,
                        machine,
                        agg_geom,
                        quality_models,
                        material_group,
                        batch_size,
                    )

                    for tr_list in op_transition_combos:
                        op_sol = OperationSolution(
                            operation_id=op_id,
                            name=op_name,
                            machine_id=machine_id,
                            fixture_id=fixture_id,
                            setup_method_id=sm_id,
                            transitions=tr_list,
                            setup_time_min=fixture.get("setup_time_min", 0.0) + sm.get("time_min", 0.0),
                            setup_cost_kzt=fixture.get("setup_cost_kzt", 0.0) + sm.get("cost_kzt", 0.0),
                            setup_error_mm=sm.get("setup_error_mm", 0.0),
                            machine_positioning_mm=machine.get("accuracy", {}).get("positioning_mm", 0.02),
                            machine_minute_cost_kzt=machine.get("cost", {}).get("machine_minute_cost_kzt", 0.0),
                        )
                        op_options.append(op_sol)

        if op_options:
            per_op_options.append(op_options)

    import random

    if not per_op_options:
        return []

    # Combine one option per operation → full solution
    solutions: List[Solution] = []
    
    total_combos = 1
    for options in per_op_options:
        total_combos *= len(options)
        
    MAX_COMBOS = 1000
    
    if total_combos <= MAX_COMBOS:
        for combo in itertools_product(*per_op_options):
            sol = Solution(
                solution_id=str(uuid.uuid4()),
                operations=list(combo),
            )
            solutions.append(sol)
    else:
        # Avoid memory explosion by random sampling
        for _ in range(MAX_COMBOS):
            combo = [random.choice(options) for options in per_op_options]
            sol = Solution(
                solution_id=str(uuid.uuid4()),
                operations=combo,
            )
            solutions.append(sol)

    return solutions


def _build_transition_combos(
    transition_templates: List[Dict],
    tools_map: Dict,
    machine: Dict,
    agg_geom: Dict,
    quality_models: Dict,
    material_group: str,
    batch_size: int,
) -> List[List[TransitionSolution]]:
    """
    For each transition template, enumerate tool × (V, f, ap) combinations.
    Returns list of [TransitionSolution, ...] lists (one per template → one per combo).
    """
    per_tr_options: List[List[TransitionSolution]] = []

    machine_caps = machine.get("capabilities", [])

    for tr_tmpl in transition_templates:
        method = tr_tmpl["method"]
        capability = _map_method_to_capability(method)

        # Check machine can perform this method
        if capability not in machine_caps:
            continue

        tr_options: List[TransitionSolution] = []
        tr_id = tr_tmpl["transition_id"]

        for tool_id in tr_tmpl.get("tool_candidates", []):
            tool = tools_map.get(tool_id)
            if not tool:
                continue
            if material_group not in tool.get("compatible_material_groups", []):
                continue

            cd = tool.get("cutting_data", {})
            V_range = cd.get("V_m_min", {"min": 50, "max": 100})
            f_range = cd.get("f_mm_rev", {"min": 0.05, "max": 0.2})
            ap_range = cd.get("ap_mm", {"min": 0.5, "max": 2.0})

            Vs = _sample_range(V_range["min"], V_range["max"], CUTTING_LEVELS)
            fs = _sample_range(f_range["min"], f_range["max"], CUTTING_LEVELS)
            aps = _sample_range(ap_range["min"], ap_range["max"], CUTTING_LEVELS)

            tool_d = tool.get("diameter_mm", 10.0)
            geom_with_tool = dict(agg_geom)
            geom_with_tool["_tool_d"] = tool_d

            for V, f, ap in itertools_product(Vs, fs, aps):
                bt = _basic_time(method, geom_with_tool, V, f, ap)
                tool_cost_per_part = (
                    (bt / (tool.get("tool_life_min", 60) + 1e-9))
                    * tool.get("tool_cost_kzt", 0.0)
                    / batch_size
                )
                ra = _roughness_for_method(method, quality_models)

                # Aggressiveness = f_used / f_max (proxy)
                agg = f / (f_range["max"] + 1e-9) * ap / (ap_range["max"] + 1e-9)
                tr_sol = TransitionSolution(
                    transition_id=tr_id,
                    method=method,
                    tool_id=tool_id,
                    V=V,
                    f=f,
                    ap=ap,
                    basic_time_min=bt,
                    tool_cost_per_part_kzt=round(tool_cost_per_part, 2),
                    achieved_ra_um=ra,
                )
                # Store aggressiveness for quality risk model
                tr_sol._cutting_aggr = round(agg, 4)  # type: ignore[attr-defined]
                tr_options.append(tr_sol)

        per_tr_options.append(tr_options)

    if not per_tr_options:
        return [[]]

    # Combine one cut-param option per transition
    return [list(combo) for combo in itertools_product(*per_tr_options)]
