"""
Pytest configuration and test database fixtures.
Provides an isolated, fully migrated database instance for testing.
"""

import os
import sys

# Ensure project root is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def test_engine():
    """
    Creates an in-memory SQLite database instance with the complete schema.
    """
    engine = create_engine("sqlite:///:memory:", echo=False)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    ddl_path = os.path.join(base_dir, "src", "ingestion", "sql", "01_create_tables.sql")

    with open(ddl_path, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # SQLite compatibility for DDL execution
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            # Clean postgres-specific syntax for in-memory sqlite tests
            sqlite_stmt = stmt.replace(" CASCADE", "").replace(" cascade", "")
            if sqlite_stmt.strip():
                conn.execute(text(sqlite_stmt))

    yield engine
    engine.dispose()

@pytest.fixture(scope="function")
def db_session(test_engine):
    """
    Provides a transactional database session rolled back after each test.
    """
    connection = test_engine.connect()
    transaction = connection.begin()
    session_factory = sessionmaker(bind=connection)
    session = session_factory()

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="session")
def raw_data_dir():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "data", "raw")
