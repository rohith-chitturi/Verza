import os

import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from storage.models.runtime import Base


def get_test_db_url():
    return os.environ.get(
        "VERZA_TEST_DATABASE_URL",
        "postgresql+psycopg://verza:verza_password@localhost:5433/verza_db"
    )

@pytest.fixture(scope="session")
def engine():
    db_url = get_test_db_url()
    eng = create_engine(db_url)
    try:
        # Test connection
        with eng.connect():
            pass
    except OperationalError as e:
        pytest.fail(f"ENVIRONMENT DEPENDENCY FAILURE: PostgreSQL is unavailable at {db_url}. Please ensure docker-compose up -d postgres is running. Details: {e}")
    
    # In a real environment we would use Alembic. 
    # For testing isolation, we can create all tables cleanly here on the test database schema.
    # To avoid dropping production data, we should ensure the test DB is separate. 
    # Since we are using the primary dev DB, we will rely on metadata.create_all for missing tables.
    Base.metadata.drop_all(eng)
    Base.metadata.create_all(eng)
    
    yield eng
    
    Base.metadata.drop_all(eng)

@pytest.fixture
def session_factory(engine):
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)

@pytest.fixture
def repo(session_factory):
    from storage.catalog.sql_repository import RunSqlRepository
    return RunSqlRepository(session_factory)

@pytest.fixture
def workflow_repo(session_factory):
    from storage.catalog.sql_repository import WorkflowSqlRepository
    return WorkflowSqlRepository(session_factory)
