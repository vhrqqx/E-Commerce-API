from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
import sys
from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(BASE_DIR)

load_dotenv(os.path.join(BASE_DIR, ".env"))

DB_USER=os.getenv("DB_USER", "postgres")
DB_PASSWORD=os.getenv("DB_PASSWORD", "postgrespwd")
DB_HOST=os.getenv("DB_HOST", "localhost")
DB_PORT=os.getenv("DB_PORT", "5432")
DB_NAME=os.getenv("DB_NAME", "ecommerce")

POSTGRESQL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(POSTGRESQL_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()