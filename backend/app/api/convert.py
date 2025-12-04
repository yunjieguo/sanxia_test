"""文件转换 API 路由"""
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import os

from ..database import get_db
from ..services.converter import ConverterService
from ..schemas.conversion import (
    ConvertToPdfRequest,
    ConvertToPdfResponse,
    ConversionResponse,
    ConversionStatusResponse
)

router = APIRouter(prefix="/api/convert", tags=["文件转换"])


@router.post("/to-pdf", response_model=ConvertToPdfResponse, summary="转换为PDF")
async def convert_to_pdf(
    request: ConvertToPdfRequest,
    db: Session = Depends(get_db)
):
    """
    将文件转换为 PDF

    支持的格式：
    - 图片：PNG, JPG, JPEG, GIF, BMP
    - 文档：DOC, DOCX

    Args:
        request: 转换请求（包含文件ID）
        db: 数据库会话

    Returns:
        ConvertToPdfResponse: 转换任务信息
    """
    from ..models.file import File
    from ..utils.file_utils import get_file_extension

    converter = ConverterService(db)

    try:
        # 获取文件信息以确定文件类型
        db_file = db.query(File).filter(File.id == request.file_id).first()
        if not db_file:
            raise HTTPException(status_code=404, detail="文件不存在")

        file_ext = get_file_extension(db_file.original_name)

        # 根据文件类型选择转换方法
        if file_ext in ['png', 'jpg', 'jpeg', 'gif', 'bmp']:
            conversion = converter.convert_image_to_pdf(request.file_id)
        elif file_ext in ['doc', 'docx']:
            conversion = converter.convert_word_to_pdf(request.file_id)
        else:
            raise HTTPException(status_code=400, detail=f"不支持的文件格式: {file_ext}")

        return ConvertToPdfResponse(
            message="转换任务已完成" if conversion.status == "completed" else "转换任务创建成功",
            conversion_id=conversion.id,
            status=conversion.status
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"转换失败: {str(e)}")


@router.get("/status/{conversion_id}", response_model=ConversionStatusResponse, summary="查询转换状态")
async def get_conversion_status(
    conversion_id: int,
    db: Session = Depends(get_db)
):
    """
    查询转换任务状态

    Args:
        conversion_id: 转换任务ID
        db: 数据库会话

    Returns:
        ConversionStatusResponse: 转换状态信息
    """
    converter = ConverterService(db)
    conversion = converter.get_conversion_by_id(conversion_id)

    if not conversion:
        raise HTTPException(status_code=404, detail="转换任务不存在")

    # 构建结果URL
    result_url = None
    if conversion.status == "completed" and conversion.result_filename:
        result_url = f"/api/convert/download/{conversion.id}"

    return ConversionStatusResponse(
        conversion_id=conversion.id,
        file_id=conversion.file_id,
        status=conversion.status,
        progress=100 if conversion.status == "completed" else 0,
        error_message=conversion.error_message,
        result_url=result_url
    )


@router.get("/result/{conversion_id}", response_model=ConversionResponse, summary="获取转换结果")
async def get_conversion_result(
    conversion_id: int,
    db: Session = Depends(get_db)
):
    """
    获取转换结果详情

    Args:
        conversion_id: 转换任务ID
        db: 数据库会话

    Returns:
        ConversionResponse: 转换结果详情
    """
    converter = ConverterService(db)
    conversion = converter.get_conversion_by_id(conversion_id)

    if not conversion:
        raise HTTPException(status_code=404, detail="转换任务不存在")

    return ConversionResponse.model_validate(conversion)


@router.get("/download/{conversion_id}", summary="下载转换结果")
async def download_conversion_result(
    conversion_id: int,
    db: Session = Depends(get_db)
):
    """
    下载转换后的文件

    Args:
        conversion_id: 转换任务ID
        db: 数据库会话

    Returns:
        FileResponse: 文件流
    """
    converter = ConverterService(db)
    conversion = converter.get_conversion_by_id(conversion_id)

    if not conversion:
        raise HTTPException(status_code=404, detail="转换任务不存在")

    if conversion.status != "completed":
        raise HTTPException(status_code=400, detail="转换未完成")

    if not conversion.result_path or not os.path.exists(conversion.result_path):
        raise HTTPException(status_code=404, detail="转换结果文件不存在")

    # 获取原文件名（不含扩展名）+ .pdf
    from ..models.file import File
    original_file = db.query(File).filter(File.id == conversion.file_id).first()
    if original_file:
        base_name = os.path.splitext(original_file.original_name)[0]
        download_filename = f"{base_name}.pdf"
    else:
        download_filename = conversion.result_filename

    return FileResponse(
        path=conversion.result_path,
        filename=download_filename,
        media_type="application/pdf"
    )


@router.delete("/{conversion_id}", summary="删除转换任务")
async def delete_conversion(
    conversion_id: int,
    db: Session = Depends(get_db)
):
    """
    删除转换任务及其结果文件

    Args:
        conversion_id: 转换任务ID
        db: 数据库会话

    Returns:
        删除结果
    """
    converter = ConverterService(db)
    success = converter.delete_conversion(conversion_id)

    if not success:
        raise HTTPException(status_code=404, detail="转换任务不存在")

    return {"message": "转换任务删除成功", "conversion_id": conversion_id}
