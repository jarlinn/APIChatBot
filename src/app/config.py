"""
Application configuration
Handles environment variables and database configurations
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration using Pydantic Settings"""
    
    # db configs
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # PostgreSQL params
    postgres_host: str = Field(env="POSTGRES_HOST")
    postgres_port: int = Field(env="POSTGRES_PORT")
    postgres_user: str = Field(env="POSTGRES_USER")
    postgres_password: str = Field(env="POSTGRES_PASSWORD")
    postgres_db: str = Field(env="POSTGRES_DB")
    
    # JWT
    secret_key: str = Field(env="SECRET_KEY")
    
    # MinIO/S3
    minio_endpoint: str = Field(env="MINIO_ENDPOINT")
    minio_access_key: str = Field(env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(env="MINIO_SECRET_KEY")
    minio_bucket_name: str = Field(env="MINIO_BUCKET_NAME")
    minio_secure: bool = Field(env="MINIO_SECURE")

    # N8N
    n8n_webhook: Optional[str] = Field(default=None, env="N8N_WEBHOOK")

    # Gemini
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # Email
    email_provider: str = Field(default="console", env="EMAIL_PROVIDER")
    email_from_name: str = Field(default="ChatBot UFPS", env="EMAIL_FROM_NAME")
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    mailtrap_host: str = Field(default="sandbox.smtp.mailtrap.io", env="MAILTRAP_HOST")
    mailtrap_port: int = Field(default=2525, env="MAILTRAP_PORT")
    mailtrap_username: str = Field(default="", env="MAILTRAP_USERNAME")
    mailtrap_password: str = Field(default="", env="MAILTRAP_PASSWORD")
    mailtrap_from_email: str = Field(default="noreply@chatbot.ufps.edu.co", env="MAILTRAP_FROM_EMAIL")

    # Default Admin
    admin_view: str = Field(default="", env="ADMIN_VIEW_TOKEN")
    
    # CORS
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )
    
    @property
    def postgresql_url(self) -> str:
        """Build a PostgreSQL URL for asyncpg"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def postgresql_sync_url(self) -> str:
        """Construye la URL de PostgreSQL para psycopg2 (migraciones)"""
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

# Global Instance
settings = Settings()
