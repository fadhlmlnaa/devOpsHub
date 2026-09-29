import os
import re
from typing import Optional, List
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Environment
    APP_ENV: str = "development"
    ENVIRONMENT: str = "development"  # Backward compatibility alias

    # PostgreSQL Database
    DATABASE_URL_OVERRIDE: Optional[str] = None
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "devops"
    DATABASE_USER: str = "devops"
    DATABASE_PASSWORD: str = "change_me"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    DATABASE_POOL_TIMEOUT: int = 30

    # Redis Cache & Background Queue
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_MAX_CONNECTIONS: int = 20

    # Application Server Concurrency
    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    WEB_CONCURRENCY: int = 2
    REQUEST_TIMEOUT_SECONDS: int = 60

    # JWT Authentication
    JWT_SECRET_KEY: str = "change_me_super_secret_jwt_key_at_least_32_chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # SSH & Credential Encryption
    CREDENTIAL_ENCRYPTION_KEY: str = "vXv6c8b-vHqIeD_66QvG7F-80hZ-0sX0lJ3Y1kQ9cZg="
    AGENT_SECRET_KEY: str = "change_me_agent_hmac_secret_key_production_32_chars"

    # Connection & Command Timeouts (Seconds)
    SSH_CONNECT_TIMEOUT: int = 10
    SSH_COMMAND_TIMEOUT: int = 15
    MONITORING_CONNECT_TIMEOUT: int = 5
    MONITORING_COMMAND_TIMEOUT: int = 5
    SERVICE_CONNECTION_TIMEOUT: int = 5
    SERVICE_COMMAND_TIMEOUT: int = 10
    LOG_CONNECTION_TIMEOUT: int = 5
    LOG_COMMAND_TIMEOUT: int = 10
    MAX_LOG_RESPONSE_BYTES: int = 1048576

    # Docker Settings
    DOCKER_CONNECTION_TIMEOUT: int = 5
    DOCKER_COMMAND_TIMEOUT: int = 15
    DOCKER_LOG_COMMAND_TIMEOUT: int = 10
    MAX_DOCKER_LOG_RESPONSE_BYTES: int = 1048576
    DOCKER_COMPOSE_COMMAND_TIMEOUT: int = 60

    # Deployment Settings
    DEPLOYMENT_CONNECTION_TIMEOUT: int = 5
    DEPLOYMENT_COMMAND_TIMEOUT: int = 60
    DEPLOYMENT_MAX_DURATION: int = 1800
    MAX_DEPLOYMENT_LOG_LINES: int = 5000
    MAX_DEPLOYMENT_LOG_MESSAGE_LENGTH: int = 4000

    # Backup Settings
    BACKUP_CONNECTION_TIMEOUT: int = 5
    BACKUP_COMMAND_TIMEOUT: int = 300
    BACKUP_MAX_DURATION: int = 3600
    MAX_BACKUP_LOG_LINES: int = 5000
    MAX_BACKUP_LOG_MESSAGE_LENGTH: int = 4000

    # Alerts & Notifications
    ALERT_EVALUATION_INTERVAL_SECONDS: int = 60
    ALERT_DEFAULT_DURATION_SECONDS: int = 60
    ALERT_ENABLE_BACKGROUND_SCHEDULER: bool = True
    MAX_NOTIFICATIONS_LIMIT: int = 100

    # Security Hardening & Rate Limiting
    CORS_ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:8000,http://127.0.0.1:3000,http://127.0.0.1:8000"
    SECURITY_HEADERS_ENABLED: bool = True
    HSTS_ENABLED: bool = False
    AUTH_RATE_LIMIT_ENABLED: bool = True
    AUTH_LOGIN_RATE_LIMIT: int = 10  # max requests per minute per IP
    AUTH_REGISTER_RATE_LIMIT: int = 5  # max requests per minute per IP
    AUTH_REFRESH_RATE_LIMIT: int = 20  # max requests per minute per IP
    OPERATION_RATE_LIMIT: int = 30  # max requests per minute per IP for sensitive operations

    # Audit & Log Retention Policies
    AUDIT_LOG_ENABLED: bool = True
    AUDIT_DEFAULT_LIMIT: int = 50
    AUDIT_MAX_LIMIT: int = 100
    AUDIT_RETENTION_DAYS: int = 90
    JOB_RETENTION_DAYS: int = 60

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def is_production(self) -> bool:
        env = (self.APP_ENV or self.ENVIRONMENT).lower()
        return env in ("production", "prod")

    @property
    def cors_origins(self) -> List[str]:
        if not self.CORS_ALLOWED_ORIGINS:
            return ["http://localhost:3000", "http://127.0.0.1:3000"]
        return [origin.strip() for origin in self.CORS_ALLOWED_ORIGINS.split(",") if origin.strip()]

    @property
    def database_url(self) -> str:
        if self.DATABASE_URL_OVERRIDE:
            return self.DATABASE_URL_OVERRIDE
        env_db_url = os.getenv("DATABASE_URL")
        if env_db_url:
            return env_db_url
        return (
            f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )

    def validate_production_settings(self) -> List[str]:
        """Validates critical security settings for production readiness.
        
        Returns a list of validation failure error messages.
        """
        errors = []
        if not self.is_production:
            return errors

        insecure_patterns = ["change_me", "secret", "example", "default", "development", "dev-insecure"]

        # 1. JWT Secret Key Validation
        if len(self.JWT_SECRET_KEY) < 32:
            errors.append("JWT_SECRET_KEY harus memiliki panjang minimal 32 karakter pada environment production.")
        for pat in insecure_patterns:
            if pat in self.JWT_SECRET_KEY.lower():
                errors.append(f"JWT_SECRET_KEY mengandung nilai tidak aman ('{pat}') pada production.")
                break

        # 2. Credential Encryption Key Validation
        default_fernet = "vXv6c8b-vHqIeD_66QvG7F-80hZ-0sX0lJ3Y1kQ9cZg="
        if self.CREDENTIAL_ENCRYPTION_KEY == default_fernet:
            errors.append("CREDENTIAL_ENCRYPTION_KEY masih menggunakan default placeholder. Wajib digenerate Fernet key baru untuk production.")

        # 3. Database Password Validation
        for pat in ["change_me", "postgres", "password", "root"]:
            if self.DATABASE_PASSWORD.lower() == pat:
                errors.append(f"DATABASE_PASSWORD menggunakan kata sandi default tidak aman ('{pat}') pada production.")
                break

        # 4. CORS Origins Wildcard Check
        if "*" in self.cors_origins:
            errors.append("CORS_ALLOWED_ORIGINS tidak boleh memuat wildcard '*' pada environment production.")

        return errors


settings = Settings()
