
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg://chamados_user:senha_local_chamados@localhost:5433/chamados_db",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
)

Base = declarative_base()


def get_db():
    """Fornece uma sessão do banco para cada requisição."""
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()
