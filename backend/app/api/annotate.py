"""标注 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db
from ..models.annotation import Annotation, Template
from ..models.file import File
from ..schemas.annotation import (
    AnnotationCreate,
    AnnotationUpdate,
    AnnotationResponse,
    AnnotationListResponse,
    BatchAnnotationCreate,
    TemplateCreate,
    TemplateUpdate,
    TemplateResponse,
    TemplateListResponse,
    ApplyTemplateRequest,
    ApplyTemplateResponse
)

router = APIRouter(prefix="/api/annotations", tags=["标注管理"])
template_router = APIRouter(prefix="/api/templates", tags=["模板管理"])


def _to_response(annotation: Annotation) -> AnnotationResponse:
    """将数据库对象转成 Pydantic 响应，并解析坐标字段"""
    try:
        coordinates = json.loads(annotation.coordinates) if annotation.coordinates else {}
    except Exception:
        coordinates = {}

    return AnnotationResponse(
        id=annotation.id,
        file_id=annotation.file_id,
        page_number=annotation.page_number,
        annotation_type=annotation.annotation_type,
        field_name=annotation.field_name,
        field_value=annotation.field_value,
        coordinates=coordinates,
        created_at=annotation.created_at,
        updated_at=annotation.updated_at,
    )


def _template_to_response(template: Template) -> TemplateResponse:
    """解析模板数据 JSON，避免前端拿到原始字符串"""
    try:
        template_data = json.loads(template.template_data) if template.template_data else {}
    except Exception:
        template_data = {}

    return TemplateResponse(
        id=template.id,
        template_name=template.template_name,
        document_type=template.document_type,
        description=template.description,
        template_data=template_data,
        created_at=template.created_at,
        updated_at=template.updated_at,
    )


# ==================== 标注相关接口 ====================

@router.post("", response_model=AnnotationResponse, summary="创建标注")
async def create_annotation(
    annotation: AnnotationCreate,
    db: Session = Depends(get_db)
):
    """
    创建单个标注

    Args:
        annotation: 标注数据
        db: 数据库会话

    Returns:
        创建的标注信息
    """
    # 检查文件是否存在
    file = db.query(File).filter(File.id == annotation.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 创建标注记录
    db_annotation = Annotation(
        file_id=annotation.file_id,
        page_number=annotation.page_number,
        annotation_type=annotation.annotation_type,
        field_name=annotation.field_name,
        field_value=annotation.field_value,
        coordinates=json.dumps(annotation.coordinates.model_dump())
    )

    db.add(db_annotation)
    db.commit()
    db.refresh(db_annotation)

    return _to_response(db_annotation)


@router.post("/batch", response_model=AnnotationListResponse, summary="批量创建标注")
async def create_annotations_batch(
    batch: BatchAnnotationCreate,
    db: Session = Depends(get_db)
):
    """
    批量创建标注

    Args:
        batch: 批量标注数据
        db: 数据库会话

    Returns:
        创建的标注列表
    """
    # 检查文件是否存在
    file = db.query(File).filter(File.id == batch.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    created_annotations = []

    for ann_data in batch.annotations:
        db_annotation = Annotation(
            file_id=batch.file_id,
            page_number=ann_data["page_number"],
            annotation_type=ann_data["annotation_type"],
            field_name=ann_data["field_name"],
            field_value=ann_data.get("field_value"),
            coordinates=json.dumps(ann_data["coordinates"])
        )
        db.add(db_annotation)
        created_annotations.append(db_annotation)

    db.commit()

    for ann in created_annotations:
        db.refresh(ann)

    return AnnotationListResponse(
        annotations=[_to_response(ann) for ann in created_annotations],
        total=len(created_annotations)
    )


@router.get("/file/{file_id}", response_model=AnnotationListResponse, summary="获取文件的所有标注")
async def get_file_annotations(
    file_id: int,
    page_number: int = Query(None, description="页码筛选"),
    db: Session = Depends(get_db)
):
    """
    获取指定文件的所有标注

    Args:
        file_id: 文件ID
        page_number: 可选的页码筛选
        db: 数据库会话

    Returns:
        标注列表
    """
    # 检查文件是否存在
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 查询标注
    query = db.query(Annotation).filter(Annotation.file_id == file_id)

    if page_number is not None:
        query = query.filter(Annotation.page_number == page_number)

    annotations = query.order_by(Annotation.page_number, Annotation.created_at).all()

    return AnnotationListResponse(
        annotations=[_to_response(ann) for ann in annotations],
        total=len(annotations)
    )


@router.get("/{annotation_id}", response_model=AnnotationResponse, summary="获取标注详情")
async def get_annotation(
    annotation_id: int,
    db: Session = Depends(get_db)
):
    """
    获取标注详情

    Args:
        annotation_id: 标注ID
        db: 数据库会话

    Returns:
        标注信息
    """
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="标注不存在")

    return _to_response(annotation)


@router.put("/{annotation_id}", response_model=AnnotationResponse, summary="更新标注")
async def update_annotation(
    annotation_id: int,
    annotation_update: AnnotationUpdate,
    db: Session = Depends(get_db)
):
    """
    更新标注信息

    Args:
        annotation_id: 标注ID
        annotation_update: 更新数据
        db: 数据库会话

    Returns:
        更新后的标注信息
    """
    db_annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not db_annotation:
        raise HTTPException(status_code=404, detail="标注不存在")

    # 更新字段
    update_data = annotation_update.model_dump(exclude_unset=True)

    if "coordinates" in update_data and update_data["coordinates"]:
        update_data["coordinates"] = json.dumps(update_data["coordinates"])

    for field, value in update_data.items():
        setattr(db_annotation, field, value)

    db.commit()
    db.refresh(db_annotation)

    return _to_response(db_annotation)


@router.delete("/{annotation_id}", summary="删除标注")
async def delete_annotation(
    annotation_id: int,
    db: Session = Depends(get_db)
):
    """
    删除标注

    Args:
        annotation_id: 标注ID
        db: 数据库会话

    Returns:
        删除结果
    """
    annotation = db.query(Annotation).filter(Annotation.id == annotation_id).first()
    if not annotation:
        raise HTTPException(status_code=404, detail="标注不存在")

    db.delete(annotation)
    db.commit()

    return {"message": "标注删除成功", "annotation_id": annotation_id}


@router.delete("/file/{file_id}", summary="删除文件的所有标注")
async def delete_file_annotations(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    删除指定文件的所有标注

    Args:
        file_id: 文件ID
        db: 数据库会话

    Returns:
        删除结果
    """
    # 检查文件是否存在
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 删除所有标注
    deleted_count = db.query(Annotation).filter(Annotation.file_id == file_id).delete()
    db.commit()

    return {"message": f"已删除 {deleted_count} 个标注", "file_id": file_id, "count": deleted_count}


# ==================== 模板相关接口 ====================

@template_router.post("", response_model=TemplateResponse, summary="创建模板")
async def create_template(
    template: TemplateCreate,
    db: Session = Depends(get_db)
):
    """
    创建标注模板

    Args:
        template: 模板数据
        db: 数据库会话

    Returns:
        创建的模板信息
    """
    # 检查模板名称是否已存在
    existing = db.query(Template).filter(Template.template_name == template.template_name).first()
    if existing:
        raise HTTPException(status_code=400, detail="模板名称已存在")

    # 构建模板数据
    template_data = {
        "fields": [field.model_dump() for field in template.fields]
    }

    # 创建模板记录
    db_template = Template(
        template_name=template.template_name,
        document_type=template.document_type,
        description=template.description,
        template_data=json.dumps(template_data, ensure_ascii=False)
    )

    db.add(db_template)
    db.commit()
    db.refresh(db_template)

    return _template_to_response(db_template)


@template_router.get("", response_model=TemplateListResponse, summary="获取模板列表")
async def get_templates(
    document_type: str = Query(None, description="文档类型筛选"),
    db: Session = Depends(get_db)
):
    """
    获取模板列表

    Args:
        document_type: 可选的文档类型筛选
        db: 数据库会话

    Returns:
        模板列表
    """
    query = db.query(Template)

    if document_type:
        query = query.filter(Template.document_type == document_type)

    templates = query.order_by(Template.created_at.desc()).all()

    return TemplateListResponse(
        templates=[_template_to_response(t) for t in templates],
        total=len(templates)
    )


@template_router.get("/{template_id}", response_model=TemplateResponse, summary="获取模板详情")
async def get_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    获取模板详情

    Args:
        template_id: 模板ID
        db: 数据库会话

    Returns:
        模板信息
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    return _template_to_response(template)


@template_router.put("/{template_id}", response_model=TemplateResponse, summary="更新模板")
async def update_template(
    template_id: int,
    template_update: TemplateUpdate,
    db: Session = Depends(get_db)
):
    """
    更新模板信息

    Args:
        template_id: 模板ID
        template_update: 更新数据
        db: 数据库会话

    Returns:
        更新后的模板信息
    """
    db_template = db.query(Template).filter(Template.id == template_id).first()
    if not db_template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 更新字段
    update_data = template_update.model_dump(exclude_unset=True)

    if "fields" in update_data and update_data["fields"]:
        template_data = {
            "fields": [field.model_dump() if hasattr(field, 'model_dump') else field
                      for field in update_data["fields"]]
        }
        update_data["template_data"] = json.dumps(template_data, ensure_ascii=False)
        del update_data["fields"]

    for field, value in update_data.items():
        setattr(db_template, field, value)

    db.commit()
    db.refresh(db_template)

    return _template_to_response(db_template)


@template_router.delete("/{template_id}", summary="删除模板")
async def delete_template(
    template_id: int,
    db: Session = Depends(get_db)
):
    """
    删除模板

    Args:
        template_id: 模板ID
        db: 数据库会话

    Returns:
        删除结果
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    db.delete(template)
    db.commit()

    return {"message": "模板删除成功", "template_id": template_id}


@template_router.post("/{template_id}/apply", response_model=ApplyTemplateResponse, summary="应用模板")
async def apply_template(
    template_id: int,
    request: ApplyTemplateRequest,
    db: Session = Depends(get_db)
):
    """
    应用模板到文件（自动提取信息）

    注意：此接口目前返回模板定义，实际的信息抽取功能将在后续实现

    Args:
        template_id: 模板ID
        request: 应用请求
        db: 数据库会话

    Returns:
        提取结果
    """
    # 检查模板是否存在
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    # 检查文件是否存在
    file = db.query(File).filter(File.id == request.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 基于模板字段生成标注占位（示例逻辑，可替换为真实提取）
    template_data = json.loads(template.template_data)
    fields = template_data.get("fields", [])

    created_annotations = []
    base_x, base_y = 60, 60
    gap_y = 50

    for idx, field in enumerate(fields):
        # 如果已存在同名字段的标注则跳过
        exists = db.query(Annotation).filter(
            Annotation.file_id == request.file_id,
            Annotation.field_name == field.get("field_name")
        ).first()
        if exists:
            continue

        coords = field.get("coordinates") or {
            "x": base_x,
            "y": base_y + idx * gap_y,
            "width": 180,
            "height": 36
        }
        page_number = field.get("page_number") or 1

        ann = Annotation(
            file_id=request.file_id,
            page_number=page_number,
            annotation_type=field.get("field_type", "text"),
            field_name=field.get("field_name", f"field_{idx+1}"),
            field_value="",
            coordinates=json.dumps(coords)
        )
        db.add(ann)
        created_annotations.append(ann)

    db.commit()
    for ann in created_annotations:
        db.refresh(ann)

    extracted_data = [
        {
            "field_name": ann.field_name,
            "field_value": ann.field_value or "",
            "page_number": ann.page_number,
            "coordinates": json.loads(ann.coordinates),
            "annotation_id": ann.id,
            "confidence": 0.0
        }
        for ann in created_annotations
    ]

    return ApplyTemplateResponse(
        message=f"模板应用成功，新增 {len(extracted_data)} 条标注占位",
        extracted_data=extracted_data,
        total_extracted=len(extracted_data)
    )
