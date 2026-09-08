import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

load_dotenv()

# Falls back to local Postgres for local dev; set DATABASE_URL in the
# environment (e.g. Render's Postgres connection string) for deployment.
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/ai_auth_demo",
)

# Render (and most managed Postgres providers) can close idle connections
# server-side, so pool_pre_ping avoids stale-connection errors, and
# pool_recycle keeps connections from going stale over long uptimes.
engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300)

SessionLocal = sessionmaker(bind=engine)

Base = declarative_base()