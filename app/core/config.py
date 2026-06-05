"""
Tax God - Application Configuration
Central settings management via Pydantic BaseSettings.
"""

from __future__ import annotations

from enum import Enum
from functools import lru_cache

from pydantic import field_validator
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEV = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class ModelTier(str, Enum):
    """LLM model tiers ordered by cost (lowest first)."""

    CACHE = "cache"
    BUDGET = "budget"  # GPT-4o-mini / Haiku
    STANDARD = "standard"  # Claude 3.5 Sonnet
    PREMIUM = "premium"  # GPT-4o
    HEAVY = "heavy"  # GPT-4o (extended context / complex reasoning)


class Settings(BaseSettings):
    """Global application settings loaded from environment variables."""

    # -- Application ----------------------------------------------------------
    APP_NAME: str = "Tax God"
    APP_VERSION: str = "3.0.0"
    ENVIRONMENT: Environment = Environment.DEV
    DEBUG: bool = True
    LOG_LEVEL: str = "INFO"
    SECRET_KEY: str = "CHANGE-ME-IN-PRODUCTION"
    METRICS_TOKEN: str = ""

    # -- Server ---------------------------------------------------------------
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    ALLOWED_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:8000"]

    # -- Database -------------------------------------------------------------
    DATABASE_URL: str = "postgresql+asyncpg://taxgod:taxgod123@localhost:5432/taxgod"
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 10

    # -- Redis ----------------------------------------------------------------
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600  # 1 hour default

    # -- Neo4j ----------------------------------------------------------------
    NEO4J_URI: str = "bolt://localhost:7687"
    NEO4J_USER: str = "neo4j"
    NEO4J_PASSWORD: str = "taxgod123"

    # -- Elasticsearch --------------------------------------------------------
    ELASTICSEARCH_URL: str = "http://localhost:9200"

    # -- LLM API Keys --------------------------------------------------------
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""

    # -- LLM Model Configuration ----------------------------------------------
    MODEL_GPT4O: str = "gpt-4o"
    MODEL_GPT4O_MINI: str = "gpt-4o-mini"
    MODEL_CLAUDE_SONNET: str = "claude-3-5-sonnet-20241022"
    MODEL_CLAUDE_HAIKU: str = "claude-3-5-haiku-20241022"

    # -- Cost Governor --------------------------------------------------------
    COST_SOFT_LIMIT_PER_QUERY: float = 0.50
    COST_SOFT_LIMIT_PER_COMPLEX_TASK: float = 2.00
    COST_SOFT_LIMIT_PER_CLIENT_MONTH: float = 100.00
    COST_HARD_LIMIT_DAILY: float = 200.00
    COST_EMERGENCY_RESERVE: float = 10.00
    CACHE_HIT_TARGET: float = 0.75
    SWARM_PARALLEL_THRESHOLD: int = 70
    SWARM_MIN_BATCH_SIZE: int = 5
    COST_SWARM_BASE: float = 0.05
    COST_SWARM_PER_ITEM: float = 0.004

    # -- JWT Auth -------------------------------------------------------------
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # -- Celery / RabbitMQ ----------------------------------------------------
    CELERY_BROKER_URL: str = "amqp://guest:guest@localhost:5672//"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # -- Document Storage -----------------------------------------------------
    S3_BUCKET: str = "taxgod-documents"
    S3_REGION: str = "us-east-1"
    MAX_UPLOAD_SIZE_MB: int = 50

    # -- Integrations ---------------------------------------------------------
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/callback"

    QUICKBOOKS_CLIENT_ID: str = ""
    QUICKBOOKS_CLIENT_SECRET: str = ""
    QUICKBOOKS_REDIRECT_URI: str = "http://localhost:8000/api/v1/integrations/callback"
    INTEGRATION_ENCRYPTION_KEY: str = ""
    # Same key as Trinity: VAULT_MASTER_KEY (AES-256 vault encryption). Used for credential encryption when set.
    VAULT_MASTER_KEY: str = ""

    # -- Outreach / Lead Sources ----------------------------------------------
    SENDGRID_API_KEY: str = ""
    APOLLO_API_KEY: str = ""

    # -- Stripe (subscription billing) ----------------------------------------
    STRIPE_SECRET_KEY: str = ""
    STRIPE_PUBLISHABLE_KEY: str = ""
    STRIPE_WEBHOOK_SECRET: str = ""
    STRIPE_PRICE_MONTHLY: str = ""  # Stripe Price ID for monthly plan

    # -- Model Pricing (per 1M tokens, as of Feb 2026) -----------------------
    PRICING_GPT4O_INPUT: float = 2.50
    PRICING_GPT4O_OUTPUT: float = 10.00
    PRICING_GPT4O_MINI_INPUT: float = 0.15
    PRICING_GPT4O_MINI_OUTPUT: float = 0.60
    PRICING_CLAUDE_SONNET_INPUT: float = 3.00
    PRICING_CLAUDE_SONNET_OUTPUT: float = 15.00
    PRICING_CLAUDE_HAIKU_INPUT: float = 0.25
    PRICING_CLAUDE_HAIKU_OUTPUT: float = 1.25

    # -- Embedding Model ------------------------------------------------------
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    EMBEDDING_DIMENSIONS: int = 3072

    @field_validator(
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "INTEGRATION_ENCRYPTION_KEY",
        "VAULT_MASTER_KEY",
        "SENDGRID_API_KEY",
        "APOLLO_API_KEY",
        "STRIPE_SECRET_KEY",
        "STRIPE_PUBLISHABLE_KEY",
        "STRIPE_WEBHOOK_SECRET",
        "STRIPE_PRICE_MONTHLY",
        mode="before",
    )
    @classmethod
    def _allow_empty_keys(cls, v: str) -> str:
        return v or ""

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == Environment.PRODUCTION

    @field_validator("SECRET_KEY", mode="after")
    @classmethod
    def _check_secret_key(cls, v: str, info) -> str:
        env = info.data.get("ENVIRONMENT")
        if env == Environment.PRODUCTION and (not v or v == "CHANGE-ME-IN-PRODUCTION" or len(v) < 32):
            raise ValueError(
                "SECRET_KEY must be a strong random string (>=32 chars) in production. "
                "Generate with: openssl rand -hex 32"
            )
        return v

    @field_validator("DEBUG", mode="after")
    @classmethod
    def _check_debug(cls, v: bool, info) -> bool:
        env = info.data.get("ENVIRONMENT")
        if env == Environment.PRODUCTION and v:
            raise ValueError("DEBUG must be false in production")
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True


@lru_cache
def get_settings() -> Settings:
    """Return cached singleton settings instance."""
    return Settings()
