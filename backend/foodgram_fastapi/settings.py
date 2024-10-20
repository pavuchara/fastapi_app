import os

from dotenv import load_dotenv


load_dotenv()


# DB settings:
POSTGRES_DB = os.getenv("POSTGRES_DB", "FastAPI")
POSTGRES_USER = os.getenv("POSTGRES_USER", "FastAPI")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "FastAPI")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
DATABASE_URL = f"postgresql+asyncpg://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:5432/{POSTGRES_DB}"

# CORS:
ALLOW_ORIGINS = ["*"]  # TODO Fix me later
ALLOWED_HOSTS = ["*"]  # TODO Fix me later
