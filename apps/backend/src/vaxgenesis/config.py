"""Config stub (audit v1.1).

In the deployed repository, the full Settings lives at
`vaxgenesis/config.py`. This stub provides the minimal fields that
audit-v1.1 modules reference.
"""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    secret_key: str = "dev-secret-key-not-for-production-must-be-32chars-or-more"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60
    cors_origins: list[str] = ["http://localhost:3000"]

    postgres_host: str = "postgres"
    postgres_port: int = 5432
    postgres_db: str = "vaxgenesis"
    postgres_user: str = "vaxgenesis"
    postgres_password: str = "vaxgenesis"
    database_url: str = "postgresql+psycopg://vaxgenesis:vaxgenesis@postgres:5432/vaxgenesis"

    redis_host: str = "redis"
    redis_port: int = 6379
    redis_password: str = ""
    redis_url: str = "redis://redis:6379/0"

    neo4j_host: str = "neo4j"
    neo4j_port: int = 7687
    neo4j_user: str = "neo4j"
    neo4j_password: str = "neo4jpass"
    neo4j_uri: str = "bolt://neo4j:7687"

    environment: str = "development"
    log_level: str = "info"
    log_format: str = "json"


settings = Settings()
