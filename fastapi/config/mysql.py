from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from config.config import load_config

DATABASE_URL = load_config("database")["mysql"]["url"]

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()