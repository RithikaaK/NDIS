"""Application Configuration using Pydantic Settings."""
import urllib.parse
from typing import List , Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment or .env file."""
    
    PROJECT_NAME: str = "NDIS Management System"
    API_V1_STR: str = "/api/v1"
    
    # Database Settings (MSSQL via pyodbc)
    DB_SERVER: str = r".\SQLEXPRESS"
    REDIS_URL: str = "redis://localhost:6379/0"
    DB_NAME: str = "NDIS_DB"
    DB_USER: Optional[str] = None
    DB_PASSWORD: Optional[str] = None
    DB_DRIVER: str = "ODBC Driver 17 for SQL Server"
    DB_TRUSTED_CONNECTION: bool = True
    
    # Security Settings
    SECRET_KEY: str = "your-secret-key-min-32-chars-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # Email / OTP settings
    RESEND_API_KEY: str = ""
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASS: str = ""
    EMAIL_FROM_NAME: str = "NDIS Manager"
    DEV_REDIRECT_EMAIL: str = ""  # If set, all OTPs are sent here (dev/testing only)
    
    # Frontend URL — used in emails so links point to the React app, not the API
    FRONTEND_URL: str = "http://localhost:5173"

    # Backend URL — used for set-password page link in welcome emails
    BACKEND_URL: str = "http://localhost:8000"

    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
    ]
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )
    
    @property
    def DATABASE_URL(self) -> str:
        """Constructs synchronous SQLAlchemy connection URL for MSSQL via pyodbc using odbc_connect."""
        # Clean driver string (strip curly braces if present)
        driver = self.DB_DRIVER.strip("{}")
        
        # Build standard ODBC connection string
        conn_parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={self.DB_SERVER}",
            f"DATABASE={self.DB_NAME}",
        ]
        
        # Use Windows Authentication if DB_TRUSTED_CONNECTION is True or if DB_USER is empty
        if self.DB_TRUSTED_CONNECTION or not self.DB_USER:
            conn_parts.append("Trusted_Connection=yes")
        else:
            conn_parts.append(f"UID={self.DB_USER}")
            conn_parts.append(f"PWD={self.DB_PASSWORD or ''}")

        conn_parts.append("TrustServerCertificate=yes")
        conn_parts.append("MARS_Connection=yes")

        odbc_str = ";".join(conn_parts) + ";"
        encoded_params = urllib.parse.quote_plus(odbc_str)
        return f"mssql+pyodbc:///?odbc_connect={encoded_params}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Constructs async SQLAlchemy connection URL for MSSQL via aioodbc using odbc_connect."""
        driver = self.DB_DRIVER.strip("{}")
        conn_parts = [
            f"DRIVER={{{driver}}}",
            f"SERVER={self.DB_SERVER}",
            f"DATABASE={self.DB_NAME}",
        ]
        if self.DB_TRUSTED_CONNECTION or not self.DB_USER:
            conn_parts.append("Trusted_Connection=yes")
        else:
            conn_parts.append(f"UID={self.DB_USER}")
            conn_parts.append(f"PWD={self.DB_PASSWORD or ''}")
        conn_parts.append("TrustServerCertificate=yes")
        conn_parts.append("MARS_Connection=yes")
        odbc_str = ";".join(conn_parts) + ";"
        encoded_params = urllib.parse.quote_plus(odbc_str)
        return f"mssql+aioodbc:///?odbc_connect={encoded_params}"


settings = Settings()
