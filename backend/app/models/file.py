"""文件数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, BigInteger
from datetime import datetime
from ..database import Base


class File(Base):
    """文件记录表"""
    __tablename__ = "files"

    id = Column(Integer, primary_key=True, index=True, comment="文件ID")
    filename = Column(String(255), nullable=False, comment="存储文件名（带UUID）")
    original_name = Column(String(255), nullable=False, comment="原始文件名")
    file_type = Column(String(50), nullable=False, comment="文件类型（pdf/png/jpg等）")
    file_size = Column(BigInteger, nullable=False, comment="文件大小（字节）")
    file_path = Column(String(500), nullable=False, comment="文件存储路径")
    status = Column(String(50), default="uploaded", comment="文件状态（uploaded/converting/converted/failed）")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<File(id={self.id}, filename={self.filename}, type={self.file_type})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "filename": self.filename,
            "original_name": self.original_name,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "file_path": self.file_path,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
