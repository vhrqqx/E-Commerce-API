import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import sys
import os

# test/ is inside src/, so '..' resolves to src/ — which contains main.py, models.py, security.py, and db/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import models
from db.databases import get_db, Base
from main import app

DB_USER=os.getenv("DB_USER", "postgres")
DB_PASSWORD=os.getenv("DB_PASSWORD", "1234567")
DB_HOST=os.getenv("DB_HOST", "localhost")
DB_PORT=os.getenv("DB_PORT", "5432")
DB_NAME=os.getenv("DB_NAME", "ecommerce")

POSTGRESQL_DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(
    POSTGRESQL_DATABASE_URL,
    poolclass=StaticPool,
)

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
