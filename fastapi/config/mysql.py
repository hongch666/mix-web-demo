from sqlmodel import create_engine, Session
from typing import Generator
from config import load_config

DATABASE_URL: str = load_config("database")["mysql"]["url"]
engine = create_engine(DATABASE_URL, echo=True)

def get_db() -> Generator[Session, None, None]:
    with Session(engine) as session:
        yield session