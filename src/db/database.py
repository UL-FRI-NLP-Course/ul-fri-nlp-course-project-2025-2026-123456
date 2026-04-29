import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from src.config import DB_URL

# Use SQLite locally if no DB_URL provided
db_url = DB_URL or "sqlite:///" + os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "data", "cars.db"
)

engine = create_engine(db_url, echo=False)
SessionLocal = sessionmaker(bind=engine)


def init_db():
    from src.db.models import Base
    Base.metadata.create_all(bind=engine)


def get_session():
    return SessionLocal()