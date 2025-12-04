"""文件处理服务"""
import os
import uuid
import shutil
from typing import Optional
from fastapi import UploadFile, HTTPException
from sqlalchemy.orm import Session
from pathlib import Path

from ..config import settings
from ..models.file import File


class FileHandler:
    """文件处理器"""

    def __init__(self, db: Session):
        self.db = db

    @staticmethod
    def validate_file_type(filename: str) -> bool:
        """
        验证文件类型

        Args:
            filename: 文件名

        Returns:
            bool: 是否为允许的文件类型
        """
        file_ext = Path(filename).suffix.lower().lstrip(".")
        allowed_extensions = settings.get_allowed_extensions()
        return file_ext in allowed_extensions

    @staticmethod
    def validate_file_size(file_size: int) -> bool:
        """
        验证文件大小

        Args:
            file_size: 文件大小（字节）

        Returns:
            bool: 是否在允许范围内
        """
        return file_size <= settings.MAX_UPLOAD_SIZE

    @staticmethod
    def get_file_extension(filename: str) -> str:
        """
        获取文件扩展名

        Args:
            filename: 文件名

        Returns:
            str: 文件扩展名（不含点号）
        """
        return Path(filename).suffix.lower().lstrip(".")

    @staticmethod
    def generate_safe_filename(original_filename: str) -> str:
        """
        生成安全的文件名（UUID + 原扩展名）

        Args:
            original_filename: 原始文件名

        Returns:
            str: 安全的文件名
        """
        file_ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex
        return f"{unique_id}{file_ext}"

    async def save_upload_file(self, upload_file: UploadFile) -> File:
        """
        保存上传的文件

        Args:
            upload_file: FastAPI UploadFile 对象

        Returns:
            File: 文件记录对象

        Raises:
            HTTPException: 文件验证失败或保存失败
        """
        # 验证文件类型
        if not self.validate_file_type(upload_file.filename):
            raise HTTPException(
                status_code=400,
                detail=f"不支持的文件类型。允许的类型：{settings.ALLOWED_EXTENSIONS}"
            )

        # 读取文件内容以获取大小
        content = await upload_file.read()
        file_size = len(content)

        # 验证文件大小
        if not self.validate_file_size(file_size):
            raise HTTPException(
                status_code=400,
                detail=f"文件大小超过限制。最大允许：{settings.MAX_UPLOAD_SIZE / 1024 / 1024:.2f}MB"
            )

        # 生成安全文件名
        safe_filename = self.generate_safe_filename(upload_file.filename)
        file_path = os.path.join(settings.UPLOAD_DIR, safe_filename)

        # 保存文件
        try:
            with open(file_path, "wb") as f:
                f.write(content)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

        # 创建数据库记录
        file_type = self.get_file_extension(upload_file.filename)
        db_file = File(
            filename=safe_filename,
            original_name=upload_file.filename,
            file_type=file_type,
            file_size=file_size,
            file_path=file_path,
            status="uploaded"
        )

        try:
            self.db.add(db_file)
            self.db.commit()
            self.db.refresh(db_file)
        except Exception as e:
            # 如果数据库操作失败，删除已保存的文件
            if os.path.exists(file_path):
                os.remove(file_path)
            raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")

        return db_file

    def get_file_by_id(self, file_id: int) -> Optional[File]:
        """
        根据 ID 获取文件记录

        Args:
            file_id: 文件ID

        Returns:
            Optional[File]: 文件记录对象，不存在返回 None
        """
        return self.db.query(File).filter(File.id == file_id).first()

    def get_all_files(self, skip: int = 0, limit: int = 100) -> list[File]:
        """
        获取所有文件列表

        Args:
            skip: 跳过的记录数
            limit: 返回的最大记录数

        Returns:
            list[File]: 文件列表
        """
        return self.db.query(File).offset(skip).limit(limit).all()

    def get_files_count(self) -> int:
        """
        获取文件总数

        Returns:
            int: 文件总数
        """
        return self.db.query(File).count()

    def delete_file(self, file_id: int) -> bool:
        """
        删除文件（数据库记录和物理文件）

        Args:
            file_id: 文件ID

        Returns:
            bool: 是否删除成功

        Raises:
            HTTPException: 文件不存在或删除失败
        """
        db_file = self.get_file_by_id(file_id)
        if not db_file:
            raise HTTPException(status_code=404, detail="文件不存在")

        # 删除物理文件
        if os.path.exists(db_file.file_path):
            try:
                os.remove(db_file.file_path)
            except Exception as e:
                raise HTTPException(status_code=500, detail=f"删除文件失败: {str(e)}")

        # 删除数据库记录
        try:
            self.db.delete(db_file)
            self.db.commit()
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"数据库操作失败: {str(e)}")

        return True

    @staticmethod
    def is_archive_file(filename: str) -> bool:
        """
        判断是否为压缩包文件

        Args:
            filename: 文件名

        Returns:
            bool: 是否为压缩包
        """
        file_ext = Path(filename).suffix.lower().lstrip(".")
        return file_ext in ["zip", "rar"]

    @staticmethod
    def is_image_file(filename: str) -> bool:
        """
        判断是否为图片文件

        Args:
            filename: 文件名

        Returns:
            bool: 是否为图片
        """
        file_ext = Path(filename).suffix.lower().lstrip(".")
        return file_ext in ["png", "jpg", "jpeg"]

    @staticmethod
    def is_pdf_file(filename: str) -> bool:
        """
        判断是否为 PDF 文件

        Args:
            filename: 文件名

        Returns:
            bool: 是否为 PDF
        """
        file_ext = Path(filename).suffix.lower().lstrip(".")
        return file_ext == "pdf"

    @staticmethod
    def is_office_file(filename: str) -> bool:
        """
        判断是否为 Office 文档

        Args:
            filename: 文件名

        Returns:
            bool: 是否为 Office 文档
        """
        file_ext = Path(filename).suffix.lower().lstrip(".")
        return file_ext in ["doc", "docx"]
