"""文件相关 Schema"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class FileUploadResponse(BaseModel):
    """文件上传响应"""
    id: int = Field(..., description="文件ID")
    filename: str = Field(..., description="存储文件名")
    original_name: str = Field(..., description="原始文件名")
    file_type: str = Field(..., description="文件类型")
    file_size: int = Field(..., description="文件大小（字节）")
    file_path: str = Field(..., description="文件路径")
    status: str = Field(default="uploaded", description="文件状态")
    created_at: datetime = Field(..., description="创建时间")

    class Config:
        from_attributes = True


class FileInfoResponse(BaseModel):
    """文件信息响应"""
    id: int
    filename: str
    original_name: str
    file_type: str
    file_size: int
    file_path: str
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FileListResponse(BaseModel):
    """文件列表响应"""
    total: int = Field(..., description="总数量")
    files: list[FileInfoResponse] = Field(..., description="文件列表")


class FileDeleteResponse(BaseModel):
    """文件删除响应"""
    message: str = Field(..., description="响应消息")
    file_id: int = Field(..., description="文件ID")
