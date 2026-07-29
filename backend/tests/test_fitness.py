"""
Unit tests for fitness evaluation functions.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.models.domain import Solution, OperationSolution, TransitionSolution
from app.optimizer.fitness import evaluate


QUALITY_MODELS = {
    "quality_risk": {
        "weights": {
            "setup_error_mm": 0.45,
            "machine_positioning_mm": 0.35,
            "aggressive_cutting_penalty": 0.20,
        }
    }
}


def make_full_solution(
    basic_time=5.0,
    machine_rate=200.0,
    setup_time=6.0,
    setup_cost=800.0,
    setup_error=0.02,
    machine_pos=0.01,
    tool_cost_per_part=50.0,
):
    tr = TransitionSolution(
        transition_id="TR1",
        method="face_milling_finish",
        tool_id="T_FACE_063",
        V=180.0,
        f=0.25,
        ap=1.5,
        basic_time_min=basic_time,
        tool_cost_per_part_kzt=tool_cost_per_part,
        achieved_ra_um=1.6,
    )
    tr._cutting_aggr = 0.5  # type: ignore
    op = OperationSolution(
        operation_id="OP10",
        name="Test Op",
        machine_id="VMC_3AX_01",
        fixture_id="VISE_160",
        setup_method_id="PROBE_WCS",
        transitions=[tr],
        setup_time_min=setup_time,
        setup_cost_kzt=setup_cost,
        setup_error_mm=setup_error,
        machine_positioning_mm=machine_pos,
        machine_minute_cost_kzt=machine_rate,
    )
    sol = Solution(solution_id="test_sol")
    sol.operations = [op]
    return sol


class TestTimeCalculation:
    def test_basic_time_plus_aux(self):
        sol = make_full_solution(basic_time=10.0, setup_time=5.0)
        evaluate(sol, QUALITY_MODELS, batch_size=1)
        # time = setup(5) + basic(10) + aux(10*0.2=2) = 17
        assert abs(sol.time_total_min - 17.0) < 0.01

    def test_zero_basic_time(self):
        sol = make_full_solution(basic_time=0.0, setup_time=3.0)
        evaluate(sol, QUALITY_MODELS, batch_size=1)
        assert sol.time_total_min == pytest.approx(3.0, abs=0.01)


class TestCostCalculation:
    def test_cost_includes_machine_rate(self):
        sol = make_full_solution(
            basic_time=10.0,
            machine_rate=200.0,
            setup_cost=800.0,
            tool_cost_per_part=50.0,
        )
        evaluate(sol, QUALITY_MODELS, batch_size=1)
        # machine_cost = 12 min * 200 = 2400; setup=800; tool=50
        expected = 800.0 + 2400.0 + 50.0
        assert abs(sol.cost_total_min - expected) < 1.0

    def test_free_machine_only_setup_and_tool_cost(self):
        sol = make_full_solution(basic_time=5.0, machine_rate=0.0, setup_cost=500.0, tool_cost_per_part=0.0)
        evaluate(sol, QUALITY_MODELS, batch_size=1)
        assert sol.cost_total_min == pytest.approx(500.0, abs=0.01)


class TestSetupError:
    def test_setup_error_reflected(self):
        sol = make_full_solution(setup_error=0.04)
        evaluate(sol, QUALITY_MODELS, batch_size=1)
        assert sol.setup_error_min == pytest.approx(0.04)

    def test_max_setup_error_across_ops(self):
        sol = make_full_solution(setup_error=0.02)
        # Add second op with higher error
        op2 = OperationSolution(
            operation_id="OP20", name="Op2",
            machine_id="VMC_3AX_02", fixture_id="VISE_160", setup_method_id="EDGE_FINDER_WCS",
            setup_error_mm=0.08, machine_positioning_mm=0.015, machine_minute_cost_kzt=180.0,
        )
        sol.operations.append(op2)
        evaluate(sol, QUALITY_MODELS, batch_size=1)
        assert sol.setup_error_min == pytest.approx(0.08)


class TestQualityRisk:
    def test_quality_risk_zero_aggressiveness(self):
        sol = make_full_solution(setup_error=0.02, machine_pos=0.01)
        sol.operations[0].transitions[0]._cutting_aggr = 0.0  # type: ignore
        evaluate(sol, QUALITY_MODELS, batch_size=1)
        # risk = 0.45*(0.02/0.10) + 0.35*(0.01/0.025) + 0.20*0 = 0.09+0.14 = 0.23
        assert sol.quality_risk_min == pytest.approx(0.23, abs=0.01)
