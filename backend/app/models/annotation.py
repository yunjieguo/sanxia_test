"""标注数据模型"""
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class Annotation(Base):
    """标注记录表"""
    __tablename__ = "annotations"

    id = Column(Integer, primary_key=True, index=True, comment="标注ID")
    file_id = Column(Integer, ForeignKey("files.id", ondelete="CASCADE"), nullable=False, comment="关联文件ID")
    page_number = Column(Integer, nullable=False, comment="页码（从1开始）")
    annotation_type = Column(String(50), nullable=False, comment="标注类型（text/long_text/image/table）")
    field_name = Column(String(100), nullable=False, comment="字段名称（name/date/number/amount等）")
    field_value = Column(Text, nullable=True, comment="字段值（可选）")
    image_path = Column(String(500), nullable=True, comment="图片路径（当标注类型为image时使用）")
    coordinates = Column(Text, nullable=False, comment="坐标信息（JSON格式：{x, y, width, height}）")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    # 关系
    file = relationship("File", backref="annotations")

    def __repr__(self):
        return f"<Annotation(id={self.id}, file_id={self.file_id}, page={self.page_number}, type={self.annotation_type})>"

    def to_dict(self):
        """转换为字典"""
        import json
        return {
            "id": self.id,
            "file_id": self.file_id,
            "page_number": self.page_number,
            "annotation_type": self.annotation_type,
            "field_name": self.field_name,
            "field_value": self.field_value,
            "image_path": self.image_path,
            "coordinates": json.loads(self.coordinates) if self.coordinates else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }


class Template(Base):
    """标注模板表"""
    __tablename__ = "templates"

    id = Column(Integer, primary_key=True, index=True, comment="模板ID")
    template_name = Column(String(100), nullable=False, unique=True, comment="模板名称")
    document_type = Column(String(50), nullable=False, comment="文档类型（contract/invoice等）")
    description = Column(Text, nullable=True, comment="模板描述")
    template_data = Column(Text, nullable=False, comment="模板数据（JSON格式，包含所有字段定义）")
    created_at = Column(DateTime, default=datetime.now, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, comment="更新时间")

    def __repr__(self):
        return f"<Template(id={self.id}, name={self.template_name}, type={self.document_type})>"

    def to_dict(self):
        """转换为字典"""
        import json
        return {
            "id": self.id,
            "template_name": self.template_name,
            "document_type": self.document_type,
            "description": self.description,
            "template_data": json.loads(self.template_data) if self.template_data else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
