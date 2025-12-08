"""标注相关的 Pydantic Schema"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


# ==================== 标注 Schema ====================

class CoordinatesSchema(BaseModel):
    """坐标信息"""
    x: float = Field(..., description="X坐标")
    y: float = Field(..., description="Y坐标")
    width: float = Field(..., description="宽度")
    height: float = Field(..., description="高度")
    font_size: float | None = Field(None, description="显示字体大小")
    font_color: Optional[str] = Field(None, description="字体颜色")
    font_family: Optional[str] = Field(None, description="字体")

    class Config:
        json_schema_extra = {
            "example": {
                "x": 100.5,
                "y": 200.3,
                "width": 150.0,
                "height": 50.0,
                "font_size": 12,
                "font_color": "#333333",
                "font_family": "Arial"
            }
        }


class AnnotationCreate(BaseModel):
    """创建标注请求"""
    file_id: int = Field(..., description="文件ID")
    page_number: int = Field(..., ge=1, description="页码（从1开始）")
    annotation_type: str = Field(..., description="标注类型（text/long_text/image/table）")
    field_name: str = Field(..., description="字段名称")
    field_value: Optional[str] = Field(None, description="字段值")
    image_path: Optional[str] = Field(None, description="图片路径（当标注类型为image时使用）")
    coordinates: CoordinatesSchema = Field(..., description="坐标信息")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": 1,
                "page_number": 1,
                "annotation_type": "text",
                "field_name": "contract_name",
                "field_value": "采购合同",
                "coordinates": {
                    "x": 100.5,
                    "y": 200.3,
                    "width": 150.0,
                    "height": 50.0
                }
            }
        }


class AnnotationUpdate(BaseModel):
    """更新标注请求"""
    page_number: Optional[int] = Field(None, ge=1, description="页码")
    annotation_type: Optional[str] = Field(None, description="标注类型")
    field_name: Optional[str] = Field(None, description="字段名称")
    field_value: Optional[str] = Field(None, description="字段值")
    image_path: Optional[str] = Field(None, description="图片路径")
    coordinates: Optional[CoordinatesSchema] = Field(None, description="坐标信息")


class AnnotationResponse(BaseModel):
    """标注响应"""
    id: int
    file_id: int
    page_number: int
    annotation_type: str
    field_name: str
    field_value: Optional[str] = None
    image_path: Optional[str] = None
    coordinates: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class AnnotationListResponse(BaseModel):
    """标注列表响应"""
    annotations: List[AnnotationResponse]
    total: int


class BatchAnnotationCreate(BaseModel):
    """批量创建标注请求"""
    file_id: int = Field(..., description="文件ID")
    annotations: List[Dict[str, Any]] = Field(..., description="标注列表")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": 1,
                "annotations": [
                    {
                        "page_number": 1,
                        "annotation_type": "text",
                        "field_name": "contract_name",
                        "field_value": "采购合同",
                        "coordinates": {"x": 100, "y": 200, "width": 150, "height": 50}
                    },
                    {
                        "page_number": 1,
                        "annotation_type": "text",
                        "field_name": "contract_date",
                        "field_value": "2025-12-04",
                        "coordinates": {"x": 300, "y": 200, "width": 100, "height": 30}
                    }
                ]
            }
        }


# ==================== 模板 Schema ====================

class FieldDefinition(BaseModel):
    """字段定义"""
    field_name: str = Field(..., description="字段名称")
    field_type: str = Field(..., description="字段类型（text/long_text/image/table）")
    required: bool = Field(default=False, description="是否必填")
    description: Optional[str] = Field(None, description="字段描述")
    page_number: Optional[int] = Field(None, ge=1, description="默认页码")
    coordinates: Optional[Dict[str, Any]] = Field(
        None, description="默认坐标/样式 {x,y,width,height,font_size,font_color,font_family}"
    )
    field_value: Optional[str] = Field(None, description="默认字段值")
    image_path: Optional[str] = Field(None, description="图片字段的存储路径")
    keywords: Optional[List[str]] = Field(None, description="关键词/锚点词（支持多个备选）")
    page_hint: Optional[int] = Field(None, ge=1, description="优先匹配的页码提示")
    anchor_offset: Optional[Dict[str, float]] = Field(None, description="锚点到目标框左上角的偏移量 {x,y}")
    context_before: Optional[str] = Field(None, description="锚点前的上下文片段，用于模糊匹配")
    context_after: Optional[str] = Field(None, description="锚点后的上下文片段，用于模糊匹配")
    confidence_threshold: Optional[float] = Field(None, ge=0.0, le=1.0, description="低于该置信度标记为低可信")
    table_meta: Optional[Dict[str, Any]] = Field(None, description="表格元数据 {rows, cols, headers[]}")
    long_text: Optional[Dict[str, Any]] = Field(None, description="长文本配置 {max_lines,end_keywords[]}")


class TemplateCreate(BaseModel):
    """创建模板请求"""
    template_name: str = Field(..., min_length=1, max_length=100, description="模板名称")
    document_type: str = Field(..., description="文档类型（contract/invoice等）")
    description: Optional[str] = Field(None, description="模板描述")
    fields: List[FieldDefinition] = Field(..., description="字段定义列表")
    paint_data: Optional[List[Dict[str, Any]]] = Field(None, description="画笔数据")

    class Config:
        json_schema_extra = {
            "example": {
                "template_name": "标准采购合同",
                "document_type": "contract",
                "description": "用于采购合同的标注模板",
                "fields": [
                    {
                        "field_name": "contract_name",
                        "field_type": "text",
                        "required": True,
                        "description": "合同名称"
                    },
                    {
                        "field_name": "contract_date",
                        "field_type": "text",
                        "required": True,
                        "description": "合同日期"
                    },
                    {
                        "field_name": "contract_amount",
                        "field_type": "text",
                        "required": True,
                        "description": "合同金额"
                    }
                ]
            }
        }


class TemplateUpdate(BaseModel):
    """更新模板请求"""
    template_name: Optional[str] = Field(None, min_length=1, max_length=100, description="模板名称")
    document_type: Optional[str] = Field(None, description="文档类型")
    description: Optional[str] = Field(None, description="模板描述")
    fields: Optional[List[FieldDefinition]] = Field(None, description="字段定义列表")
    paint_data: Optional[List[Dict[str, Any]]] = Field(None, description="画笔数据")


class TemplateResponse(BaseModel):
    """模板响应"""
    id: int
    template_name: str
    document_type: str
    description: Optional[str] = None
    template_data: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TemplateListResponse(BaseModel):
    """模板列表响应"""
    templates: List[TemplateResponse]
    total: int


class ApplyTemplateRequest(BaseModel):
    """应用模板请求"""
    file_id: int = Field(..., description="文件ID")

    class Config:
        json_schema_extra = {
            "example": {
                "file_id": 1
            }
        }


class ApplyTemplateResponse(BaseModel):
    """应用模板响应"""
    message: str
    extracted_data: List[Dict[str, Any]]
    total_extracted: int
    paint_data: Optional[List[Dict[str, Any]]] = Field(None, description="画笔数据")
    match_details: Optional[List[Dict[str, Any]]] = Field(None, description="匹配说明（字段、策略、置信度等）")

    class Config:
        json_schema_extra = {
            "example": {
                "message": "模板应用成功",
                "extracted_data": [
                    {
                        "field_name": "contract_name",
                        "field_value": "采购合同",
                        "page_number": 1,
                        "confidence": 0.95
                    }
                ],
                "total_extracted": 1
            }
        }


class ApplyTemplateLLMRequest(BaseModel):
    """使用大模型应用模板"""
    file_id: int = Field(..., description="目标文件ID")
    template_id: Optional[int] = Field(None, description="模板ID（可选，缺省时使用路径参数）")
    model_name: Optional[str] = Field(None, description="可覆盖默认模型名，如 qwen-vl-max")
    top_k: int = Field(default=1, ge=1, le=5, description="每字段返回的候选数量")
    image_width: int = Field(default=1024, ge=256, le=2048, description="传给模型的页面截图宽度上限")


class ApplyTemplateLLMResponse(BaseModel):
    """大模型匹配返回"""
    message: str
    applied_annotations: List[AnnotationResponse]
    match_details: List[Dict[str, Any]] = Field(default_factory=list, description="匹配详情，含 field/page/bbox_norm/text/confidence")


# ==================== 画笔 Schema ====================

class PaintData(BaseModel):
    """画笔数据"""
    strokes: List[Dict[str, Any]] = Field(default_factory=list, description="画笔轨迹列表")

    class Config:
        json_schema_extra = {
            "example": {
                "strokes": [
                    {"type": "free", "color": "#ff0000", "width": 2, "points": [{"x": 10, "y": 20}, {"x": 30, "y": 40}]},
                    {"type": "rect", "color": "#00ff00", "width": 3, "rect": {"x": 50, "y": 60, "width": 100, "height": 80}}
                ]
            }
        }
