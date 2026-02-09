from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://tracegreens:tracegreens@db:5432/tracegreens"
    PORT: int = 8000
    APP_NAME: str = "TraceGreens"
    SEED_WEIGHT_G: float = 25.0
    TARGET_PRICE_PER_G: float = 1.6  # ₹1,600/kg
    ADMIN_PASSWORD: str = "tracegreens2026"
    # Cloudflare R2 (S3-compatible) — optional, only needed for photo uploads
    R2_ACCOUNT_ID: str = ""
    R2_ACCESS_KEY_ID: str = ""
    R2_SECRET_ACCESS_KEY: str = ""
    R2_BUCKET_NAME: str = ""
    R2_PUBLIC_URL: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"


# Fix Railway's postgres:// → postgresql:// (SQLAlchemy 2.0 requires postgresql://)
settings = Settings()
if settings.DATABASE_URL.startswith("postgres://"):
    settings.DATABASE_URL = settings.DATABASE_URL.replace("postgres://", "postgresql://", 1)
