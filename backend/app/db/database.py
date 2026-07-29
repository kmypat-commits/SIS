import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

def _db_path():
    url = os.getenv("DATABASE_URL")
    if url:
        return url
    if os.getenv("VERCEL"):
        return "sqlite:////tmp/machopt.db"
    return "sqlite:///./machopt.db"

DATABASE_URL = _db_path()

connect_args = {}
if DATABASE_URL.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
