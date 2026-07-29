"""
CRUD helpers for knowledge-base entities.
"""
from sqlalchemy.orm import Session
from .orm_models import MachineORM, FixtureORM, SetupMethodORM, ToolORM, ProjectORM
from typing import List, Optional


# ── Projects ────────────────────────────────────────────────────────────────

def get_all_projects(db: Session) -> List[ProjectORM]:
    return db.query(ProjectORM).all()

def get_project(db: Session, project_id: str) -> Optional[ProjectORM]:
    return db.query(ProjectORM).filter(ProjectORM.project_id == project_id).first()

def upsert_project(db: Session, data: dict) -> ProjectORM:
    proj = db.query(ProjectORM).filter(ProjectORM.project_id == data["project_id"]).first()
    if not proj:
        proj = ProjectORM()
        db.add(proj)
    for k, v in data.items():
        # Do not overwrite json blobs with None, prevents accidental data wipes
        if k.endswith("_json") and v is None:
            continue
        setattr(proj, k, v)
    db.commit()
    db.refresh(proj)
    return proj

def delete_project(db: Session, project_id: str) -> bool:
    proj = get_project(db, project_id)
    if proj:
        db.delete(proj)
        db.commit()
        return True
    return False


# ── Machines ─────────────────────────────────────────────────────────────────

def get_all_machines(db: Session) -> List[MachineORM]:
    return db.query(MachineORM).all()

def get_machine(db: Session, machine_id: str) -> Optional[MachineORM]:
    return db.query(MachineORM).filter(MachineORM.machine_id == machine_id).first()

def upsert_machine(db: Session, data: dict) -> MachineORM:
    m = db.query(MachineORM).filter(MachineORM.machine_id == data["machine_id"]).first()
    if not m:
        m = MachineORM()
        db.add(m)
    for k, v in data.items():
        if hasattr(m, k):
            setattr(m, k, v)
    db.commit()
    db.refresh(m)
    return m

def delete_machine(db: Session, machine_id: str) -> bool:
    m = get_machine(db, machine_id)
    if m:
        db.delete(m)
        db.commit()
        return True
    return False


# ── Fixtures ─────────────────────────────────────────────────────────────────

def get_all_fixtures(db: Session) -> List[FixtureORM]:
    return db.query(FixtureORM).all()

def get_fixture(db: Session, fixture_id: str) -> Optional[FixtureORM]:
    return db.query(FixtureORM).filter(FixtureORM.fixture_id == fixture_id).first()

def upsert_fixture(db: Session, data: dict) -> FixtureORM:
    fx = db.query(FixtureORM).filter(FixtureORM.fixture_id == data["fixture_id"]).first()
    if not fx:
        fx = FixtureORM()
        db.add(fx)
    for k, v in data.items():
        if hasattr(fx, k):
            setattr(fx, k, v)
    db.commit()
    db.refresh(fx)
    return fx

def delete_fixture(db: Session, fixture_id: str) -> bool:
    fx = get_fixture(db, fixture_id)
    if fx:
        db.delete(fx)
        db.commit()
        return True
    return False


# ── Setup Methods ─────────────────────────────────────────────────────────────

def get_all_setup_methods(db: Session) -> List[SetupMethodORM]:
    return db.query(SetupMethodORM).all()

def get_setup_method(db: Session, mid: str) -> Optional[SetupMethodORM]:
    return db.query(SetupMethodORM).filter(SetupMethodORM.setup_method_id == mid).first()

def upsert_setup_method(db: Session, data: dict) -> SetupMethodORM:
    sm = db.query(SetupMethodORM).filter(SetupMethodORM.setup_method_id == data["setup_method_id"]).first()
    if not sm:
        sm = SetupMethodORM()
        db.add(sm)
    for k, v in data.items():
        if hasattr(sm, k):
            setattr(sm, k, v)
    db.commit()
    db.refresh(sm)
    return sm

def delete_setup_method(db: Session, mid: str) -> bool:
    sm = get_setup_method(db, mid)
    if sm:
        db.delete(sm)
        db.commit()
        return True
    return False


# ── Tools ─────────────────────────────────────────────────────────────────────

def get_all_tools(db: Session) -> List[ToolORM]:
    return db.query(ToolORM).all()

def get_tool(db: Session, tool_id: str) -> Optional[ToolORM]:
    return db.query(ToolORM).filter(ToolORM.tool_id == tool_id).first()

def upsert_tool(db: Session, data: dict) -> ToolORM:
    t = db.query(ToolORM).filter(ToolORM.tool_id == data["tool_id"]).first()
    if not t:
        t = ToolORM()
        db.add(t)
    for k, v in data.items():
        if hasattr(t, k):
            setattr(t, k, v)
    db.commit()
    db.refresh(t)
    return t

def delete_tool(db: Session, tool_id: str) -> bool:
    t = get_tool(db, tool_id)
    if t:
        db.delete(t)
        db.commit()
        return True
    return False
