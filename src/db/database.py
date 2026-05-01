import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from src.config import DATA_DIR

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.carapi_schema import Base

CARAPI_DB_URL = os.getenv("CARAPI_DB_URL") or "sqlite:///" + os.path.join(DATA_DIR, "carapi.db")
engine = create_engine(CARAPI_DB_URL, echo=False)

SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()