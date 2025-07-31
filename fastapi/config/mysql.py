from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from config import load_config
from sqlalchemy.engine import Engine

DATABASE_URL: str = load_config("database")["mysql"]["url"]

engine: Engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal: sessionmaker = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db() -> Generator[Session, None, None]:
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()