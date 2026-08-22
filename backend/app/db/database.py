# SQLAlchemy setup, engine, and session management
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "DATABASE_URL not set. Copy .env.example to .env and fill in your credentials."
    )

ENV = os.getenv("ENV", "development")

engine = create_engine(DATABASE_URL,echo=(ENV == "development"),pool_pre_ping=True,pool_size=5,max_overflow=10)

SessionLocal = sessionmaker(autocommit=False,autoflush=False,bind=engine)

Base = declarative_base()