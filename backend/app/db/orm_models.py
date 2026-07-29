"""
SQLAlchemy ORM table definitions for the knowledge base.
"""
from sqlalchemy import (
    Column, String, Float, Integer, Boolean, JSON, ForeignKey, Text
)
from sqlalchemy.orm import relationship
from .database import Base


class ProjectORM(Base):
    __tablename__ = "projects"
    project_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    currency = Column(String, default="KZT")
    production_type = Column(String, default="serial")
    batch_size = Column(Integer, default=1)
    material_name = Column(String)
    material_group = Column(String)
    hardness_hb = Column(Integer, default=0)
    # JSON blobs for product and strategy
    product_json = Column(JSON, nullable=True)
    strategy_json = Column(JSON, nullable=True)
    resources_json = Column(JSON, nullable=True)
    process_templates_json = Column(JSON, nullable=True)
    costs_json = Column(JSON, nullable=True)
    quality_models_json = Column(JSON, nullable=True)


class MachineORM(Base):
    __tablename__ = "machines"
    machine_id = Column(String, primary_key=True)
    machine_type = Column(String)
    name = Column(String)
    capabilities = Column(JSON)        # list of strings
    workspace_mm = Column(JSON)        # {x,y,z}
    accuracy = Column(JSON)            # {positioning_mm, repeatability_mm}
    machine_minute_cost_kzt = Column(Float, default=0.0)
    coolant_supported = Column(Boolean, default=True)


class FixtureORM(Base):
    __tablename__ = "fixtures"
    fixture_id = Column(String, primary_key=True)
    fixture_type = Column(String)
    name = Column(String)
    compatible_machines = Column(JSON)
    setup_time_min = Column(Float, default=0.0)
    setup_cost_kzt = Column(Float, default=0.0)
    basing_options = Column(JSON)


class SetupMethodORM(Base):
    __tablename__ = "setup_methods"
    setup_method_id = Column(String, primary_key=True)
    name = Column(String)
    time_min = Column(Float, default=0.0)
    cost_kzt = Column(Float, default=0.0)
    setup_error_mm = Column(Float, default=0.0)


class ToolORM(Base):
    __tablename__ = "tools"
    tool_id = Column(String, primary_key=True)
    tool_type = Column(String)
    name = Column(String)
    diameter_mm = Column(Float, default=0.0)
    flutes = Column(Integer, default=0)
    coating = Column(String, default="")
    tool_cost_kzt = Column(Float, default=0.0)
    tool_life_min = Column(Float, default=0.0)
    compatible_material_groups = Column(JSON)
    cutting_data = Column(JSON)   # {V_m_min:{min,max}, f_mm_rev:{min,max}, ap_mm:{min,max}}
