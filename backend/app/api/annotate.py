"""标注 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import json
import os
import uuid

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
    ApplyTemplateResponse,
    PaintData
)
from ..config import settings
from ..services.ocr_engine import extract_text_blocks_with_fallback

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
        image_path=annotation.image_path,
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
        image_path=annotation.image_path,
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
            image_path=ann_data.get("image_path"),
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

    # 若更新了图片路径，清理旧文件
    if "image_path" in update_data and update_data["image_path"] != db_annotation.image_path:
        _safe_remove_image(db_annotation.image_path)

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

    _safe_remove_image(annotation.image_path)
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

    # 先清理图片文件
    annotations = db.query(Annotation).filter(Annotation.file_id == file_id).all()
    for ann in annotations:
        _safe_remove_image(ann.image_path)

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
    if template.paint_data:
        template_data["paint_data"] = template.paint_data

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
        if update_data.get("paint_data") is not None:
            template_data["paint_data"] = update_data["paint_data"]
        elif db_template.template_data:
            # 维持已有的画笔数据
            try:
                existing = json.loads(db_template.template_data)
                if existing.get("paint_data"):
                    template_data["paint_data"] = existing.get("paint_data")
            except Exception:
                pass
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


def _apply_template_to_file(
    template: Template,
    file: File,
    db: Session,
    use_matching: bool = False
) -> ApplyTemplateResponse:
    """
    基于模板字段生成标注占位，预留匹配扩展。
    当前版本：做简单文本层匹配（基于 PyMuPDF），找不到时回退模板坐标。
    """
    template_data = json.loads(template.template_data or "{}")
    fields = template_data.get("fields", [])
    paint_data = template_data.get("paint_data")

    created_annotations = []
    ann_conf_list = []
    match_details = []
    base_x, base_y = 60, 60
    gap_y = 50

    text_blocks = []
    if use_matching and os.path.exists(file.file_path):
        text_blocks = extract_text_blocks_with_fallback(file.file_path)

    def _match_field(field_def):
        # 默认坐标
        coords = field_def.get("coordinates") or {
            "x": base_x,
            "y": base_y,
            "width": 180,
            "height": 36
        }
        page_number = field_def.get("page_number") or 1
        confidence = field_def.get("confidence_threshold") or 0.3
        strategy = "template_coordinates"
        note = "未找到匹配，使用模板坐标"
        field_value = None

        if not use_matching or not text_blocks:
            return coords, page_number, confidence, strategy, note, field_value

        keywords = field_def.get("keywords") or [field_def.get("field_name", "")]
        keywords = [kw for kw in keywords if kw]
        anchor_offset = field_def.get("anchor_offset") or {}
        off_x = anchor_offset.get("x", 0)
        off_y = anchor_offset.get("y", 0)

        target_pages = []
        if field_def.get("page_hint"):
            target_pages = [field_def["page_hint"] - 1] if field_def["page_hint"] > 0 else []
        if not target_pages:
            target_pages = list(range(len(text_blocks)))

        found = None
        def _gather_long_text(page_blocks, start_idx, long_cfg):
            max_lines = max(int(long_cfg.get("max_lines", 5)), 1)
            end_keywords = [kw.lower() for kw in (long_cfg.get("end_keywords") or []) if kw]
            collected = []
            for blk in page_blocks[start_idx:start_idx + max_lines]:
                text = (blk["text"] or "").strip()
                if not text:
                    continue
                lower = text.lower()
                if end_keywords and any(ek in lower for ek in end_keywords):
                    break
                collected.append(text)
            return "\n".join(collected).strip() if collected else None

        for p_idx in target_pages:
            if p_idx < 0 or p_idx >= len(text_blocks):
                continue
            page_blocks = text_blocks[p_idx]
            for blk_idx, blk in enumerate(page_blocks):
                text_lower = (blk["text"] or "").lower()
                hit_kw = None
                for kw in keywords:
                    if kw.lower() in text_lower:
                        hit_kw = kw
                        break
                if hit_kw:
                    bbox = blk["bbox"]
                    width = coords.get("width") or (bbox[2] - bbox[0])
                    height = coords.get("height") or (bbox[3] - bbox[1])
                    found = {
                        "x": bbox[0] + off_x,
                        "y": bbox[1] + off_y,
                        "width": width,
                        "height": height,
                        "page_number": p_idx + 1,
                        "keyword": hit_kw
                    }

                    # 提取字段值：短文本取当前块，长文本尝试多行
                    ftype = field_def.get("field_type")
                    if ftype == "long_text":
                        long_cfg = field_def.get("long_text") or {}
                        field_value = _gather_long_text(page_blocks, blk_idx, long_cfg) or blk["text"].strip()
                    elif ftype == "text":
                        field_value = blk["text"].strip()
                    else:
                        field_value = field_def.get("field_value")
                    break
            if found:
                break

        if found:
            return (
                {
                    "x": found["x"],
                    "y": found["y"],
                    "width": found["width"],
                    "height": found["height"],
                    "font_size": coords.get("font_size"),
                    "font_color": coords.get("font_color"),
                    "font_family": coords.get("font_family")
                },
                found["page_number"],
                max(confidence, 0.8),
                "keyword_offset",
                f"命中关键词: {found['keyword']}",
                field_value
            )

        return coords, page_number, confidence, "template_coordinates", note, field_value

    for idx, field in enumerate(fields):
        field_name = field.get("field_name", f"field_{idx+1}")

        # 如果已存在同名字段的标注则跳过
        exists = db.query(Annotation).filter(
            Annotation.file_id == file.id,
            Annotation.field_name == field_name
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

        match_conf = 0.0
        strategy = "template_coordinates"
        note = None
        matched_value = None
        if use_matching:
            coords, page_number, match_conf, strategy, note, matched_value = _match_field(field)

        ann = Annotation(
            file_id=file.id,
            page_number=page_number,
            annotation_type=field.get("field_type", "text"),
            field_name=field_name,
            field_value=matched_value if matched_value is not None else field.get("field_value", ""),
            image_path=field.get("image_path"),
            coordinates=json.dumps(coords)
        )
        db.add(ann)
        created_annotations.append(ann)
        ann_conf_list.append({"field_name": field_name, "confidence": match_conf})

        if use_matching:
            match_details.append({
                "field_name": field_name,
                "page_number": page_number,
                "strategy": strategy,
                "confidence": match_conf,
                "note": note or ""
            })

    db.commit()
    for ann in created_annotations:
        db.refresh(ann)

    # 如果模板包含画笔数据，落盘到该文件
    if paint_data:
        paint_file = _get_paint_file_path(file.id)
        try:
            with open(paint_file, "w", encoding="utf-8") as f:
                json.dump({"strokes": paint_data}, f, ensure_ascii=False)
        except Exception as e:
            print(f"保存画笔数据失败: {e}")

    extracted_data = [
        {
            "field_name": ann.field_name,
            "field_value": ann.field_value or "",
            "page_number": ann.page_number,
            "coordinates": json.loads(ann.coordinates),
            "annotation_id": ann.id,
            "confidence": next((c["confidence"] for c in ann_conf_list if c["field_name"] == ann.field_name), 0.0)
        }
        for ann in created_annotations
    ]

    return ApplyTemplateResponse(
        message=f"模板应用成功，新增 {len(extracted_data)} 条标注占位",
        extracted_data=extracted_data,
        total_extracted=len(extracted_data),
        paint_data=paint_data or [],
        match_details=match_details or None
    )


@template_router.post("/{template_id}/apply", response_model=ApplyTemplateResponse, summary="应用模板")
async def apply_template(
    template_id: int,
    request: ApplyTemplateRequest,
    db: Session = Depends(get_db)
):
    """
    应用模板到文件（无匹配，直接使用模板坐标）
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    file = db.query(File).filter(File.id == request.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    return _apply_template_to_file(template, file, db, use_matching=False)


@template_router.post("/{template_id}/apply-matching", response_model=ApplyTemplateResponse, summary="应用模板并匹配")
async def apply_template_matching(
    template_id: int,
    request: ApplyTemplateRequest,
    db: Session = Depends(get_db)
):
    """
    应用模板到文件（预留匹配扩展）。
    当前版本：未集成 OCR/文本匹配，使用模板坐标回填，并返回 match_details 便于前端提示。
    """
    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    file = db.query(File).filter(File.id == request.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    return _apply_template_to_file(template, file, db, use_matching=True)


# ==================== 图片标注相关接口 ====================

# 创建标注图片存储目录
ANNOTATION_IMAGES_DIR = os.path.join(settings.UPLOAD_DIR, "annotation_images")
os.makedirs(ANNOTATION_IMAGES_DIR, exist_ok=True)
PAINT_DATA_DIR = os.path.join(settings.UPLOAD_DIR, "paint_data")
os.makedirs(PAINT_DATA_DIR, exist_ok=True)


def _safe_remove_image(image_path: str) -> None:
    """删除标注图片文件，删除数据库记录前使用"""
    if not image_path:
        return

    filename = os.path.basename(image_path)
    file_path = os.path.join(ANNOTATION_IMAGES_DIR, filename)

    try:
        if (
            os.path.exists(file_path)
            and os.path.commonpath([ANNOTATION_IMAGES_DIR, os.path.abspath(file_path)]) == os.path.abspath(ANNOTATION_IMAGES_DIR)
        ):
            os.remove(file_path)
    except Exception:
        # 记录失败即可，避免阻塞主流程
        pass


@router.post("/upload-image", summary="上传标注图片")
async def upload_annotation_image(
    file: UploadFile = FastAPIFile(...),
):
    """
    上传标注图片

    Args:
        file: 图片文件

    Returns:
        图片路径信息
    """
    # 验证文件类型
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="只允许上传图片文件")

    # 生成唯一文件名
    file_ext = os.path.splitext(file.filename)[1].lower()
    if file_ext not in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
        raise HTTPException(status_code=400, detail="不支持的图片格式")

    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    file_path = os.path.join(ANNOTATION_IMAGES_DIR, unique_filename)

    # 保存文件
    try:
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"文件保存失败: {str(e)}")

    # 返回相对路径
    relative_path = f"annotation_images/{unique_filename}"

    return {
        "message": "图片上传成功",
        "image_path": relative_path,
        "filename": file.filename,
        "size": len(content)
    }


@router.get("/images/{filename}", summary="获取标注图片")
async def get_annotation_image(filename: str):
    """
    获取标注图片

    Args:
        filename: 图片文件名

    Returns:
        图片文件
    """
    file_path = os.path.join(ANNOTATION_IMAGES_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="图片不存在")

    return FileResponse(file_path)


@router.delete("/images/{filename}", summary="删除标注图片")
async def delete_annotation_image(filename: str):
    """
    删除标注图片

    Args:
        filename: 图片文件名

    Returns:
        删除结果
    """
    file_path = os.path.join(ANNOTATION_IMAGES_DIR, filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="图片不存在")

    try:
        os.remove(file_path)
        return {"message": "图片删除成功", "filename": filename}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


# ==================== 画笔数据接口 ====================


def _get_paint_file_path(file_id: int) -> str:
    return os.path.join(PAINT_DATA_DIR, f"{file_id}.json")


@router.get("/paint/{file_id}", response_model=PaintData, summary="获取文件的画笔数据")
async def get_paint_data(file_id: int):
    file_path = _get_paint_file_path(file_id)
    if not os.path.exists(file_path):
        return PaintData(strokes=[])
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return PaintData(**data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取画笔数据失败: {str(e)}")


@router.post("/paint/{file_id}", response_model=PaintData, summary="保存文件的画笔数据")
async def save_paint_data(file_id: int, payload: PaintData):
    file_path = _get_paint_file_path(file_id)
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload.model_dump(), f, ensure_ascii=False)
        return payload
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存画笔数据失败: {str(e)}")
