"""文件上传 API 路由"""
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..services.file_handler import FileHandler
from ..schemas.file import (
    FileUploadResponse,
    FileInfoResponse,
    FileListResponse,
    FileDeleteResponse
)

router = APIRouter(prefix="/api", tags=["文件上传"])


@router.post("/upload", response_model=FileUploadResponse, summary="上传文件")
async def upload_file(
    file: UploadFile = File(..., description="上传的文件"),
    db: Session = Depends(get_db)
):
    """
    上传文件接口

    支持的文件类型：pdf, png, jpg, jpeg, doc, docx, ofd, zip, rar
    文件大小限制：50MB

    Args:
        file: 上传的文件
        db: 数据库会话

    Returns:
        FileUploadResponse: 上传成功的文件信息
    """
    handler = FileHandler(db)
    db_file = await handler.save_upload_file(file)
    return FileUploadResponse.from_orm(db_file)


@router.get("/files", response_model=FileListResponse, summary="获取文件列表")
async def get_files(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """
    获取文件列表

    Args:
        skip: 跳过的记录数
        limit: 返回的最大记录数
        db: 数据库会话

    Returns:
        FileListResponse: 文件列表和总数
    """
    handler = FileHandler(db)
    files = handler.get_all_files(skip=skip, limit=limit)
    total = handler.get_files_count()

    return FileListResponse(
        total=total,
        files=[FileInfoResponse.from_orm(f) for f in files]
    )


@router.get("/files/{file_id}", response_model=FileInfoResponse, summary="获取文件详情")
async def get_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    获取文件详情

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        FileInfoResponse: 文件详细信息
    """
    handler = FileHandler(db)
    db_file = handler.get_file_by_id(file_id)

    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    return FileInfoResponse.from_orm(db_file)


@router.delete("/files/{file_id}", response_model=FileDeleteResponse, summary="删除文件")
async def delete_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    删除文件（包括数据库记录和物理文件）

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        FileDeleteResponse: 删除结果
    """
    handler = FileHandler(db)
    handler.delete_file(file_id)

    return FileDeleteResponse(
        message="文件删除成功",
        file_id=file_id
    )


@router.get("/files/{file_id}/download", summary="下载文件")
async def download_file(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    下载文件

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        FileResponse: 文件流
    """
    handler = FileHandler(db)
    db_file = handler.get_file_by_id(file_id)

    if not db_file:
        raise HTTPException(status_code=404, detail="文件不存在")

    import os
    if not os.path.exists(db_file.file_path):
        raise HTTPException(status_code=404, detail="文件不存在（物理文件缺失）")

    return FileResponse(
        path=db_file.file_path,
        filename=db_file.original_name,
        media_type="application/octet-stream"
    )


@router.delete("/files", summary="批量删除所有文件")
async def delete_all_files(
    db: Session = Depends(get_db)
):
    """
    批量删除所有文件（包括数据库记录、标注数据、转换记录和物理文件）

    注意：此操作不可逆，将删除所有已上传的文件及其相关数据

    Args:
        db: 数据库会话

    Returns:
        dict: 删除统计信息
    """
    handler = FileHandler(db)
    result = handler.delete_all_files()

    return {
        "message": "批量删除完成",
        "statistics": result
    }
