"""
Seed the database from the JSON file on first run.
"""
import json
import os
from pathlib import Path
from sqlalchemy.orm import Session
from .orm_models import (
    ProjectORM, MachineORM, FixtureORM, SetupMethodORM, ToolORM
)

SEED_FILE = Path(__file__).parent.parent.parent.parent / "data" / "machopt_mvp_0001.json"


def seed_if_empty(db: Session) -> None:
    """Load seed data into empty DB tables."""
    if db.query(ProjectORM).count() > 0:
        return  # already seeded

    if not SEED_FILE.exists():
        return

    with open(SEED_FILE, encoding="utf-8") as f:
        data = json.load(f)

    # Projects (now an array)
    for entry in data.get("projects", [data]):
        proj = entry.get("project", entry)
        mat = proj.get("material", {})
        project_orm = ProjectORM(
            project_id=proj["project_id"],
            name=proj["name"],
            currency=proj.get("currency", "KZT"),
            production_type=proj.get("production_type", "serial"),
            batch_size=proj.get("batch_size", 1),
            material_name=mat.get("name", ""),
            material_group=mat.get("group", "steel"),
            hardness_hb=mat.get("hardness_hb", 0),
            product_json=entry.get("product"),
            strategy_json=data.get("strategy"),
            resources_json=data.get("resources"),
            process_templates_json=entry.get("process_templates"),
            costs_json=data.get("costs"),
            quality_models_json=data.get("quality_models"),
        )
        db.add(project_orm)

    # Machines
    for m in data.get("resources", {}).get("machines", []):
        acc = m.get("accuracy", {})
        cost = m.get("cost", {})
        ws = m.get("workspace_mm", {})
        db.add(MachineORM(
            machine_id=m["machine_id"],
            machine_type=m.get("type", ""),
            name=m["name"],
            capabilities=m.get("capabilities", []),
            workspace_mm=ws,
            accuracy=acc,
            machine_minute_cost_kzt=cost.get("machine_minute_cost_kzt", 0.0),
            coolant_supported=m.get("coolant_supported", True),
        ))

    # Fixtures
    for fx in data.get("resources", {}).get("fixtures", []):
        db.add(FixtureORM(
            fixture_id=fx["fixture_id"],
            fixture_type=fx.get("type", ""),
            name=fx["name"],
            compatible_machines=fx.get("compatible_machines", []),
            setup_time_min=fx.get("setup_time_min", 0.0),
            setup_cost_kzt=fx.get("setup_cost_kzt", 0.0),
            basing_options=fx.get("basing_options", []),
        ))

    # Setup methods
    for sm in data.get("resources", {}).get("setup_methods", []):
        db.add(SetupMethodORM(
            setup_method_id=sm["setup_method_id"],
            name=sm["name"],
            time_min=sm.get("time_min", 0.0),
            cost_kzt=sm.get("cost_kzt", 0.0),
            setup_error_mm=sm.get("setup_error_mm", 0.0),
        ))

    # Tools
    for t in data.get("resources", {}).get("tools", []):
        db.add(ToolORM(
            tool_id=t["tool_id"],
            tool_type=t.get("type", ""),
            name=t["name"],
            diameter_mm=t.get("diameter_mm", 0.0),
            flutes=t.get("flutes", 0),
            coating=t.get("coating", ""),
            tool_cost_kzt=t.get("tool_cost_kzt", 0.0),
            tool_life_min=t.get("tool_life_min", 0.0),
            compatible_material_groups=t.get("compatible_material_groups", []),
            cutting_data=t.get("cutting_data", {}),
        ))

    db.commit()
    print("[seed] Database seeded from machopt_mvp_0001.json")
