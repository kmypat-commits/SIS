"""
Domain models for MachOpt-6L.
These are plain Python dataclasses / Pydantic models used throughout the system.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


# ─────────────────────────────────────────────
# Knowledge-base entities
# ─────────────────────────────────────────────

@dataclass
class CuttingData:
    V_min: float
    V_max: float
    f_min: float
    f_max: float
    ap_min: float
    ap_max: float


@dataclass
class Tool:
    tool_id: str
    tool_type: str
    name: str
    diameter_mm: float
    tool_cost_kzt: float
    tool_life_min: float
    compatible_material_groups: List[str]
    cutting_data: CuttingData
    flutes: int = 0
    coating: str = ""


@dataclass
class Machine:
    machine_id: str
    machine_type: str
    name: str
    capabilities: List[str]
    positioning_mm: float
    repeatability_mm: float
    machine_minute_cost_kzt: float
    coolant_supported: bool
    workspace_x: float = 0.0
    workspace_y: float = 0.0
    workspace_z: float = 0.0


@dataclass
class Fixture:
    fixture_id: str
    fixture_type: str
    name: str
    compatible_machines: List[str]
    setup_time_min: float
    setup_cost_kzt: float
    basing_options: List[str]


@dataclass
class SetupMethod:
    setup_method_id: str
    name: str
    time_min: float
    cost_kzt: float
    setup_error_mm: float


# ─────────────────────────────────────────────
# Product / CDE entities
# ─────────────────────────────────────────────

@dataclass
class CDE:
    cde_id: str
    cde_type: str
    name: str
    geometry: Dict[str, Any]
    requirements: Dict[str, Any]
    allowed_methods: List[str]


@dataclass
class Blank:
    blank_type: str
    dimensions: Dict[str, float]
    stock_allowance: Dict[str, float]


@dataclass
class Material:
    name: str
    group: str
    hardness_hb: int


@dataclass
class Product:
    product_id: str
    name: str
    blank: Blank
    cde_list: List[CDE]


@dataclass
class Project:
    project_id: str
    name: str
    currency: str
    production_type: str
    batch_size: int
    material: Material
    product: Product


# ─────────────────────────────────────────────
# Process-template entities
# ─────────────────────────────────────────────

@dataclass
class TransitionTemplate:
    transition_id: str
    method: str
    tool_candidates: List[str]
    quality_target: Dict[str, float]


@dataclass
class OperationTemplate:
    operation_id: str
    name: str
    applicable_cde: List[str]
    candidate_machines: List[str]
    candidate_fixtures: List[str]
    candidate_setup_methods: List[str]
    transitions: List[TransitionTemplate]


# ─────────────────────────────────────────────
# Solution encoding (one candidate solution)
# ─────────────────────────────────────────────

@dataclass
class TransitionSolution:
    transition_id: str
    method: str
    tool_id: str
    V: float          # cutting speed m/min
    f: float          # feed mm/rev
    ap: float         # depth of cut mm
    basic_time_min: float = 0.0
    tool_cost_per_part_kzt: float = 0.0
    achieved_ra_um: float = 0.0


@dataclass
class OperationSolution:
    operation_id: str
    name: str
    machine_id: str
    fixture_id: str
    setup_method_id: str
    transitions: List[TransitionSolution] = field(default_factory=list)
    setup_time_min: float = 0.0
    setup_cost_kzt: float = 0.0
    setup_error_mm: float = 0.0
    machine_positioning_mm: float = 0.0
    machine_minute_cost_kzt: float = 0.0


@dataclass
class Solution:
    """One complete process plan (one point in objective space)."""
    solution_id: str
    operations: List[OperationSolution] = field(default_factory=list)

    # Computed objectives — filled by fitness.py
    time_total_min: float = 0.0
    cost_total_min: float = 0.0
    setup_error_min: float = 0.0
    quality_risk_min: float = 0.0

    # Pareto tracking
    rank: int = 0
    crowding_distance: float = 0.0

    def objectives_vector(self) -> List[float]:
        return [
            self.time_total_min,
            self.cost_total_min,
            self.setup_error_min,
            self.quality_risk_min,
        ]
