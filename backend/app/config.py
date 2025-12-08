"""Application settings."""
from typing import List, Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    """Application configuration loaded from environment variables."""

    # App info
    APP_NAME: str = "PDF处理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "sqlite:///./app.db"

    # Storage
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    TEMP_DIR: str = "./temp"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    # File types
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg,doc,docx,ofd,zip,rar"

    # OCR / layout parsing
    ENABLE_OCR: bool = False
    OCR_PROVIDER: str = "paddle"  # paddle/custom
    OCR_USE_GPU: bool = False
    LAYOUTLM_MODEL_NAME: str = "microsoft/layoutlmv3-base"

    # LLM / multimodal (DashScope / Qwen)
    DASHSCOPE_API_KEY: Optional[str] = None
    DASHSCOPE_ENDPOINT: str = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
    QWEN_MODEL_NAME: str = "qwen-vl-max"

    # CORS
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_allowed_extensions(self) -> List[str]:
        """Return allowed file extensions."""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",") if ext.strip()]

    def get_cors_origins(self) -> List[str]:
        """Return allowed CORS origins."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()

# Ensure required directories exist
for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)
