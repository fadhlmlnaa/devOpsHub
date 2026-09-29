from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "devops"
    DATABASE_USER: str = "devops"
    DATABASE_PASSWORD: str = "change_me"

    BACKEND_HOST: str = "0.0.0.0"
    BACKEND_PORT: int = 8000
    ENVIRONMENT: str = "development"

    # JWT Authentication
    JWT_SECRET_KEY: str = "change_me_super_secret_jwt_key_at_least_32_chars"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 30

    # SSH & Credential Encryption
    CREDENTIAL_ENCRYPTION_KEY: str = "vXv6c8b-vHqIeD_66QvG7F-80hZ-0sX0lJ3Y1kQ9cZg="
    SSH_CONNECT_TIMEOUT: int = 10
    SSH_COMMAND_TIMEOUT: int = 15
    MONITORING_CONNECT_TIMEOUT: int = 5
    MONITORING_COMMAND_TIMEOUT: int = 5
    SERVICE_CONNECTION_TIMEOUT: int = 5
    SERVICE_COMMAND_TIMEOUT: int = 10
    LOG_CONNECTION_TIMEOUT: int = 5
    LOG_COMMAND_TIMEOUT: int = 10
    MAX_LOG_RESPONSE_BYTES: int = 1048576

    # Docker Settings (Step 10)
    DOCKER_CONNECTION_TIMEOUT: int = 5
    DOCKER_COMMAND_TIMEOUT: int = 15
    DOCKER_LOG_COMMAND_TIMEOUT: int = 10
    MAX_DOCKER_LOG_RESPONSE_BYTES: int = 1048576
    DOCKER_COMPOSE_COMMAND_TIMEOUT: int = 60

    # Deployment Settings (Step 11)
    DEPLOYMENT_CONNECTION_TIMEOUT: int = 5
    DEPLOYMENT_COMMAND_TIMEOUT: int = 60
    DEPLOYMENT_MAX_DURATION: int = 1800
    MAX_DEPLOYMENT_LOG_LINES: int = 5000
    MAX_DEPLOYMENT_LOG_MESSAGE_LENGTH: int = 4000

    # Backup Settings (Step 12)
    BACKUP_CONNECTION_TIMEOUT: int = 5
    BACKUP_COMMAND_TIMEOUT: int = 300
    BACKUP_MAX_DURATION: int = 3600
    MAX_BACKUP_LOG_LINES: int = 5000
    MAX_BACKUP_LOG_MESSAGE_LENGTH: int = 4000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
            f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}/{self.DATABASE_NAME}"
        )


settings = Settings()
