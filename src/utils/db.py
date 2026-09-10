"""
Database connection and session management for Lakers in 5.
Supports PostgreSQL production connections with SQLite fallback for local test suites.
"""

import os
import urllib.parse
from contextlib import contextmanager
from typing import Generator, Optional
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine, Connection
from sqlalchemy.orm import sessionmaker, Session
from src.utils.logging import logger

# Load environment variables
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "configs", "database.env"))

def get_database_url() -> str:
    """
    Constructs the SQLAlchemy database URL from environment variables.
    If DATABASE_URL is set, uses it directly (normalizing postgresql:// to postgresql+psycopg2://).
    Otherwise builds postgresql://user:password@host:port/dbname.
    """
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        if db_url.startswith("postgresql://"):
            return db_url.replace("postgresql://", "postgresql+psycopg2://", 1)
        return db_url

    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "lakers_in_5")
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "")

    if password:
        encoded_password = urllib.parse.quote_plus(password)
        return f"postgresql+psycopg2://{user}:{encoded_password}@{host}:{port}/{db}"
    else:
        return f"postgresql+psycopg2://{user}@{host}:{port}/{db}"

def get_engine(db_url: Optional[str] = None, echo: bool = False) -> Engine:
    """
    Creates and returns a SQLAlchemy Engine instance.
    """
    url = db_url or get_database_url()
    if url.startswith("sqlite"):
        return create_engine(url, echo=echo)
    
    return create_engine(
        url,
        echo=echo,
        pool_size=int(os.getenv("DB_POOL_SIZE", "10")),
        max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "20")),
        pool_pre_ping=True
    )

def test_connection(engine: Engine) -> bool:
    """
    Tests whether the database engine can successfully connect.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.warning(f"Database connection test failed for {engine.url}: {e}")
        return False

@contextmanager
def get_db_connection(engine: Optional[Engine] = None) -> Generator[Connection, None, None]:
    """
    Context manager for database connections.
    """
    eng = engine or get_engine()
    with eng.connect() as connection:
        yield connection

@contextmanager
def get_db_session(engine: Optional[Engine] = None) -> Generator[Session, None, None]:
    """
    Context manager for transactional database sessions.
    """
    eng = engine or get_engine()
    session_factory = sessionmaker(bind=eng)
    session = session_factory()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"Database session transaction failed: {e}")
        raise
    finally:
        session.close()

def execute_sql_file(engine: Engine, sql_filepath: str) -> None:
    """
    Executes raw SQL DDL/DML statements from an SQL file.
    """
    logger.info(f"Executing SQL file: {sql_filepath}")
    with open(sql_filepath, "r", encoding="utf-8") as f:
        sql_content = f.read()

    # Split on semicolon statements
    statements = [stmt.strip() for stmt in sql_content.split(";") if stmt.strip()]
    with engine.begin() as conn:
        for stmt in statements:
            conn.execute(text(stmt))
    logger.info(f"Successfully executed {len(statements)} statements from {os.path.basename(sql_filepath)}")

def bulk_insert_records(
    engine: Engine,
    table_name: str,
    columns: list[str],
    records: list[dict],
    on_conflict: Optional[str] = None,
    batch_size: int = 5000
) -> int:
    """
    Fast bulk insertion for PostgreSQL (via execute_values) and SQLite fallback.
    """
    if not records:
        return 0

    col_names = ", ".join(columns)
    is_postgres = "postgres" in engine.url.drivername

    if is_postgres:
        import psycopg2.extras
        # Get underlying DBAPI connection
        raw_conn = engine.raw_connection()
        try:
            with raw_conn.cursor() as cur:
                sql = f"INSERT INTO {table_name} ({col_names}) VALUES %s"
                if on_conflict:
                    sql += f" {on_conflict}"

                for i in range(0, len(records), batch_size):
                    batch = records[i:i + batch_size]
                    rows = [[rec.get(col) for col in columns] for rec in batch]
                    psycopg2.extras.execute_values(cur, sql, rows, page_size=len(batch))
            raw_conn.commit()
        except Exception:
            raw_conn.rollback()
            raise
        finally:
            raw_conn.close()
    else:
        placeholders = ", ".join([f":{col}" for col in columns])
        verb = "INSERT OR REPLACE INTO" if on_conflict else "INSERT INTO"
        sql = f"{verb} {table_name} ({col_names}) VALUES ({placeholders})"
        with engine.begin() as conn:
            for i in range(0, len(records), batch_size):
                batch = records[i:i + batch_size]
                conn.execute(text(sql), batch)

    return len(records)

