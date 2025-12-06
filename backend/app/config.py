"""应用配置文件"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """应用配置"""

    # 应用信息
    APP_NAME: str = "PDF文档处理系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 数据库配置
    DATABASE_URL: str = "sqlite:///./app.db"

    # 文件存储配置
    UPLOAD_DIR: str = "./uploads"
    OUTPUT_DIR: str = "./outputs"
    TEMP_DIR: str = "./temp"
    MAX_UPLOAD_SIZE: int = 52428800  # 50MB

    # 允许的文件类型
    ALLOWED_EXTENSIONS: str = "pdf,png,jpg,jpeg,doc,docx,ofd,zip,rar"

    # OCR / 布局解析
    ENABLE_OCR: bool = False
    OCR_PROVIDER: str = "paddle"  # paddle/custom
    OCR_USE_GPU: bool = False
    LAYOUTLM_MODEL_NAME: str = "microsoft/layoutlmv3-base"

    # CORS 配置
    CORS_ORIGINS: str = "http://localhost:5173,http://localhost:3000"

    class Config:
        env_file = ".env"
        case_sensitive = True

    def get_allowed_extensions(self) -> List[str]:
        """获取允许的文件扩展名列表"""
        return [ext.strip() for ext in self.ALLOWED_EXTENSIONS.split(",")]

    def get_cors_origins(self) -> List[str]:
        """获取 CORS 允许的源列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]


# 创建配置实例
settings = Settings()

# 确保必要的目录存在
for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
    os.makedirs(directory, exist_ok=True)
