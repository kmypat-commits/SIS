"""
Unit tests for Pareto dominance logic.
"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.optimizer.fitness import dominates, build_pareto_front
from app.models.domain import Solution


def make_sol(t, c, se, qr):
    s = Solution(solution_id=f"{t}-{c}-{se}-{qr}")
    s.time_total_min = t
    s.cost_total_min = c
    s.setup_error_min = se
    s.quality_risk_min = qr
    return s


class TestDominates:
    def test_a_dominates_b_all_better(self):
        a = [1.0, 2.0, 0.01, 0.1]
        b = [2.0, 3.0, 0.02, 0.2]
        assert dominates(a, b) is True

    def test_b_not_dominated_when_one_obj_worse(self):
        a = [1.0, 2.0, 0.01, 0.3]   # worse on quality_risk
        b = [2.0, 2.0, 0.02, 0.1]
        assert dominates(a, b) is False

    def test_equal_not_dominated(self):
        v = [1.0, 1.0, 0.01, 0.1]
        assert dominates(v, v) is False

    def test_strict_improvement_needed(self):
        a = [1.0, 2.0, 0.01, 0.1]
        b = [1.0, 2.0, 0.01, 0.1]
        # Equal in all → no dominance
        assert dominates(a, b) is False


class TestBuildParetoFront:
    def test_single_solution_in_front(self):
        s = make_sol(5, 1000, 0.02, 0.3)
        front = build_pareto_front([s])
        assert len(front) == 1
        assert front[0] is s

    def test_dominated_removed(self):
        good = make_sol(5, 1000, 0.02, 0.3)
        bad  = make_sol(10, 2000, 0.04, 0.5)   # dominated by good
        front = build_pareto_front([good, bad])
        assert good in front
        assert bad not in front

    def test_incomparable_both_in_front(self):
        s1 = make_sol(5, 2000, 0.02, 0.3)   # fast but expensive
        s2 = make_sol(10, 800, 0.02, 0.3)   # slow but cheap
        front = build_pareto_front([s1, s2])
        assert len(front) == 2

    def test_empty_input(self):
        assert build_pareto_front([]) == []

    def test_five_solutions_correct_front(self):
        solutions = [
            make_sol(5,  1000, 0.02, 0.3),   # Pareto
            make_sol(8,  700,  0.02, 0.3),   # Pareto
            make_sol(12, 500,  0.02, 0.3),   # Pareto
            make_sol(10, 1500, 0.04, 0.5),   # dominated by s1
            make_sol(9,  900,  0.03, 0.4),   # dominated by s1 on time
        ]
        front = build_pareto_front(solutions)
        # s1, s2, s3 form the front (time vs cost trade-off)
        assert len(front) >= 3
        for s in [solutions[0], solutions[1], solutions[2]]:
            assert s in front
