"""转换任务数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from datetime import datetime
from ..database import Base


class Conversion(Base):
    """转换任务表"""
    __tablename__ = "conversions"

    id = Column(Integer, primary_key=True, index=True, comment="转换任务ID")
    file_id = Column(Integer, ForeignKey("files.id"), nullable=False, comment="关联文件ID")
    source_format = Column(String(50), nullable=False, comment="源格式")
    target_format = Column(String(50), nullable=False, default="pdf", comment="目标格式")
    status = Column(
        String(50),
        default="pending",
        comment="转换状态（pending/processing/completed/failed）"
    )
    result_path = Column(String(500), nullable=True, comment="转换结果路径")
    result_filename = Column(String(255), nullable=True, comment="结果文件名")
    error_message = Column(Text, nullable=True, comment="错误信息")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    completed_at = Column(DateTime, nullable=True, comment="完成时间")

    def __repr__(self):
        return f"<Conversion(id={self.id}, file_id={self.file_id}, status={self.status})>"

    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "file_id": self.file_id,
            "source_format": self.source_format,
            "target_format": self.target_format,
            "status": self.status,
            "result_path": self.result_path,
            "result_filename": self.result_filename,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
        }
