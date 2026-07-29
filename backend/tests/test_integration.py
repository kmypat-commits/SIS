"""
Integration test: run full optimization pipeline on simplified data.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.optimizer.nsga2_solver import run_optimization


MINI_PROJECT = {
    "project": {
        "project_id": "test_mini",
        "batch_size": 10,
        "material": {"name": "Steel 45", "group": "steel", "hardness_hb": 200},
    },
    "strategy": {
        "constraints": {"allowed_machines": ["VMC_TEST"], "require_coolant": False},
        "solver": {"seed": 0, "population_size": 20, "generations": 10},
    },
    "product": {
        "cde_list": [
            {
                "cde_id": "CDE_P1",
                "type": "plane",
                "geometry": {"area_mm2": 5000.0},
                "requirements": {"roughness_ra_um": 3.2},
                "allowed_methods": ["face_milling_rough"],
            }
        ]
    },
    "resources": {
        "machines": [
            {
                "machine_id": "VMC_TEST",
                "type": "milling_3axis",
                "capabilities": ["face_milling"],
                "accuracy": {"positioning_mm": 0.01, "repeatability_mm": 0.005},
                "cost": {"machine_minute_cost_kzt": 200},
                "coolant_supported": False,
            }
        ],
        "fixtures": [
            {
                "fixture_id": "VISE_T",
                "type": "vise",
                "compatible_machines": ["VMC_TEST"],
                "setup_time_min": 5.0,
                "setup_cost_kzt": 600,
                "basing_options": ["3-2-1_standard"],
            }
        ],
        "setup_methods": [
            {"setup_method_id": "PROBE_T", "name": "Test probe", "time_min": 3.0, "cost_kzt": 300, "setup_error_mm": 0.02},
            {"setup_method_id": "EDGE_T", "name": "Edge finder", "time_min": 6.0, "cost_kzt": 200, "setup_error_mm": 0.04},
        ],
        "tools": [
            {
                "tool_id": "T_FACE_T",
                "type": "face_mill",
                "name": "Face Mill Test",
                "diameter_mm": 63.0,
                "tool_cost_kzt": 50000,
                "tool_life_min": 200,
                "compatible_material_groups": ["steel"],
                "cutting_data": {
                    "V_m_min": {"min": 120, "max": 200},
                    "f_mm_rev": {"min": 0.15, "max": 0.30},
                    "ap_mm": {"min": 1.0, "max": 2.0},
                },
            }
        ],
    },
    "process_templates": {
        "operations_catalog": [
            {
                "operation_id": "OP_T1",
                "name": "Face Plane",
                "applicable_cde": ["CDE_P1"],
                "candidate_machines": ["VMC_TEST"],
                "candidate_fixtures": ["VISE_T"],
                "candidate_setup_methods": ["PROBE_T", "EDGE_T"],
                "transitions": [
                    {
                        "transition_id": "TR_T1",
                        "method": "face_milling_rough",
                        "tool_candidates": ["T_FACE_T"],
                        "quality_target": {"roughness_ra_um": 6.3},
                    }
                ],
            }
        ]
    },
    "quality_models": {
        "roughness_estimation": {"defaults": {"face_milling_rough": {"ra_um": 6.3}}},
        "quality_risk": {"weights": {"setup_error_mm": 0.45, "machine_positioning_mm": 0.35, "aggressive_cutting_penalty": 0.20}},
    },
}


class TestFullOptimize:
    def test_pareto_front_not_empty(self):
        pareto = run_optimization(MINI_PROJECT, seed=42)
        assert len(pareto) >= 1

    def test_objectives_computed(self):
        pareto = run_optimization(MINI_PROJECT, seed=42)
        for sol in pareto:
            assert sol.time_total_min > 0
            assert sol.cost_total_min > 0
            assert 0 <= sol.setup_error_min <= 1.0
            assert 0 <= sol.quality_risk_min <= 1.0

    def test_pareto_non_dominated(self):
        """All solutions in the front should be mutually non-dominated."""
        from app.optimizer.fitness import dominates
        pareto = run_optimization(MINI_PROJECT, seed=42)
        for i, a in enumerate(pareto):
            for j, b in enumerate(pareto):
                if i != j:
                    assert not dominates(a.objectives_vector(), b.objectives_vector()), \
                        f"Solution {i} dominates {j} — front is invalid"

    def test_two_setup_methods_yield_two_groups(self):
        """Two setup methods produce different setup errors on Pareto front."""
        pareto = run_optimization(MINI_PROJECT, seed=42)
        errors = {sol.setup_error_min for sol in pareto}
        # Expect at least 2 distinct setup errors (0.02 and 0.04)
        assert len(errors) >= 2
