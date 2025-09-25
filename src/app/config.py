"""
Configuración de la aplicación
Maneja variables de entorno y configuraciones de base de datos
"""
import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Configuración de la aplicación usando Pydantic Settings"""
    
    # Configuración general
    app_name: str = Field(default="APIChatBot", env="APP_NAME")
    debug: bool = Field(default=False, env="DEBUG")
    
    # Configuración de base de datos
    database_url: str = Field(env="DATABASE_URL")
    database_echo: bool = Field(default=False, env="DATABASE_ECHO")
    
    # Configuración específica de PostgreSQL
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(env="POSTGRES_USER")
    postgres_password: str = Field(env="POSTGRES_PASSWORD")
    postgres_db: str = Field(env="POSTGRES_DB")
    
    # Pool de conexiones
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    
    # JWT
    secret_key: str = Field(env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    
    # MinIO/S3
    minio_endpoint: str = Field(default="localhost:9000", env="MINIO_ENDPOINT")
    minio_access_key: str = Field(default="minioadmin", env="MINIO_ACCESS_KEY")
    minio_secret_key: str = Field(default="minioadmin", env="MINIO_SECRET_KEY")
    minio_bucket_name: str = Field(default="chatbot-files", env="MINIO_BUCKET_NAME")
    minio_secure: bool = Field(default=False, env="MINIO_SECURE")

    
    # N8N
    n8n_webhook: Optional[str] = Field(default=None, env="N8N_WEBHOOK")

    # Gemini
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")

    # Email
    environment: str = Field(default="development", env="ENVIRONMENT")
    email_provider: str = Field(default="console", env="EMAIL_PROVIDER")
    email_from_name: str = Field(default="ChatBot UFPS", env="EMAIL_FROM_NAME")
    frontend_url: str = Field(default="http://localhost:3000", env="FRONTEND_URL")
    mailtrap_host: str = Field(default="sandbox.smtp.mailtrap.io", env="MAILTRAP_HOST")
    mailtrap_port: int = Field(default=2525, env="MAILTRAP_PORT")
    mailtrap_username: str = Field(env="MAILTRAP_USERNAME")
    mailtrap_password: str = Field(env="MAILTRAP_PASSWORD")
    mailtrap_from_email: str = Field(default="noreply@chatbot.ufps.edu.co", env="MAILTRAP_FROM_EMAIL")

    # Default Admin
    default_admin_email: str = Field(default="admin@chatbot.local", env="DEFAULT_ADMIN_EMAIL")
    default_admin_password: str = Field(default="admin123", env="DEFAULT_ADMIN_PASSWORD")
    default_admin_name: str = Field(default="Administrador", env="DEFAULT_ADMIN_NAME")
    default_admin_role: str = Field(default="admin", env="DEFAULT_ADMIN_ROLE")

    # Configuración de embeddings
    embedding_dimension: int = Field(default=384, env="EMBEDDING_DIMENSION")  # all-MiniLM-L6-v2
    max_embedding_batch_size: int = Field(default=100, env="MAX_EMBEDDING_BATCH_SIZE")
    embedding_model: str = Field(default="all-MiniLM-L6-v2", env="EMBEDDING_MODEL")
    
    # Configuración del servidor
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=8000, env="PORT")
    
    # CORS
    allowed_origins: str = Field(default="*", env="ALLOWED_ORIGINS")
    
    # Logs
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_file: str = Field(default="logs/app.log", env="LOG_FILE")
    
    # Pool de conexiones de base de datos
    db_pool_size: int = Field(default=20, env="DB_POOL_SIZE")
    db_max_overflow: int = Field(default=30, env="DB_MAX_OVERFLOW")
    db_pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    db_pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")  # 1 hora
    
    # Configuración de embeddings para alta concurrencia
    embedding_cache_size: int = Field(default=1000, env="EMBEDDING_CACHE_SIZE")
    embedding_batch_timeout: float = Field(default=5.0, env="EMBEDDING_BATCH_TIMEOUT")
    max_concurrent_embeddings: int = Field(default=10, env="MAX_CONCURRENT_EMBEDDINGS")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def postgresql_url(self) -> str:
        """Construye la URL de PostgreSQL para asyncpg"""
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
    
    def get_database_url(self) -> str:
        """
        Retorna la URL de base de datos apropiada
        Si DATABASE_URL está definida, la usa. Si no, construye la URL de PostgreSQL
        """
        if self.database_url and not self.database_url.startswith("sqlite"):
            return self.database_url
        return self.postgresql_url


# Instancia global de configuración
settings = Settings()
