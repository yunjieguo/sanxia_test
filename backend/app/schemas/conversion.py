"""转换相关的 Pydantic Schema"""
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime


class ConversionBase(BaseModel):
    """转换任务基础 Schema"""
    file_id: int
    source_format: str
    target_format: str = "pdf"


class ConversionCreate(ConversionBase):
    """创建转换任务 Schema"""
    pass


class ConversionResponse(ConversionBase):
    """转换任务响应 Schema"""
    id: int
    status: str
    result_path: Optional[str] = None
    result_filename: Optional[str] = None
    error_message: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ConversionStatusResponse(BaseModel):
    """转换状态响应 Schema"""
    conversion_id: int
    file_id: int
    status: str
    progress: Optional[int] = None
    error_message: Optional[str] = None
    result_url: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ConvertToPdfRequest(BaseModel):
    """转换为 PDF 请求 Schema"""
    file_id: int


class ConvertToPdfResponse(BaseModel):
    """转换为 PDF 响应 Schema"""
    message: str
    conversion_id: int
    status: str

    model_config = ConfigDict(from_attributes=True)
