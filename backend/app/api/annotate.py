"""标注 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List
import json
import os
import uuid
from pathlib import Path
import glob

from ..database import get_db
from ..models.annotation import Annotation, Template
from ..models.file import File
from ..models.conversion import Conversion
from ..config import settings
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


def _get_field_label(field_name: str) -> str:
    mapping = {
        "contract_name": "合同名称",
        "contract_date": "合同日期",
        "contract_number": "合同编号",
        "contract_amount": "合同金额",
        "party_a": "甲方名称",
        "party_b": "乙方名称",
    }
    return mapping.get(field_name, field_name or "")


def _choose_cjk_font():
    """尝试查找可显示中文的字体文件路径"""

    # 优先尝试的中文字体列表（按优先级排序）
    priority_fonts = [
        # 项目目录中的常见中文字体
        "simhei.ttf",      # 黑体
        "simkai.ttf",      # 楷体
        "simfang.ttf",     # 仿宋
        "simsun.ttc",      # 宋体
        "msyh.ttc",        # 微软雅黑
        "msyhbd.ttc",      # 微软雅黑粗体
        "msyhl.ttc",       # 微软雅黑细体
        "msjh.ttc",        # 微软正黑体
        "mingliub.ttc",    # 细明体
    ]

    # 在项目 backend/fonts/ 目录中查找优先字体
    backend_fonts_dir = Path(__file__).resolve().parents[2] / "fonts"

    for font_name in priority_fonts:
        # 在 backend/fonts/ 目录查找
        if backend_fonts_dir.exists():
            font_path = backend_fonts_dir / font_name
            if font_path.exists():
                print(f"[export] 找到可用中文字体: {font_path}")
                return str(font_path)

    # 系统常见中文字体
    system_fonts = [
        r"C:\Windows\Fonts\msyh.ttc",      # 微软雅黑
        r"C:\Windows\Fonts\simhei.ttf",    # 黑体
        r"C:\Windows\Fonts\simsun.ttc",    # 宋体
        r"C:\Windows\Fonts\simkai.ttf",    # 楷体
        r"/System/Library/Fonts/PingFang.ttc",           # macOS 苹方
        r"/System/Library/Fonts/STHeiti Medium.ttc",     # macOS 黑体
        r"/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc", # Linux 文泉驿
        r"/usr/share/fonts/truetype/arphic/uming.ttc",   # Linux AR PL UMing
    ]

    for path in system_fonts:
        if Path(path).exists():
            print(f"[export] 找到可用系统中文字体: {path}")
            return str(path)

    print("[export] 未找到任何可用的中文字体文件")
    return None


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


@router.get("/file/{file_id}/export", summary="导出带标注的 PDF")
async def export_annotated_pdf(
    file_id: int,
    db: Session = Depends(get_db)
):
    """
    将标注绘制到 PDF 上后导出，不影响原始文件。
    优先使用原 PDF；若原文件不是 PDF，则尝试使用最新的转换结果。
    """
    file = db.query(File).filter(File.id == file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    # 选择可用的 PDF 路径
    base_path = None
    if file.file_type.lower() == "pdf" and os.path.exists(file.file_path):
        base_path = file.file_path
    else:
        conv = (
            db.query(Conversion)
            .filter(Conversion.file_id == file_id, Conversion.status == "completed")
            .order_by(Conversion.completed_at.desc())
            .first()
        )
        if conv and conv.result_path and os.path.exists(conv.result_path):
            base_path = conv.result_path

    if not base_path:
        raise HTTPException(status_code=400, detail="未找到可用于导出的 PDF 文件，请先转换为 PDF")

    annotations = db.query(Annotation).filter(Annotation.file_id == file_id).all()
    if not annotations:
        raise HTTPException(status_code=400, detail="该文件暂无标注")

    # 生成导出路径
    output_filename = f"{uuid.uuid4()}.pdf"
    output_path = os.path.join(settings.OUTPUT_DIR, output_filename)

    try:
        import fitz
    except ImportError:
        raise HTTPException(status_code=500, detail="缺少 PyMuPDF，请先安装 pymupdf 依赖")

    try:
        doc = fitz.open(base_path)
        font_file_path = _choose_cjk_font()
        if not font_file_path:
            raise HTTPException(
                status_code=500,
                detail="未找到可用中文字体，请在 backend/fonts/ 目录或系统字体目录放置中文字体文件后重试"
            )

        # 记录每个页面是否已插入字体
        pages_with_font = set()

        for ann in annotations:
            try:
                coords = json.loads(ann.coordinates) if ann.coordinates else {}
            except Exception:
                coords = {}

            page_index = (ann.page_number or 1) - 1
            if page_index < 0 or page_index >= len(doc):
                continue

            x = coords.get("x", 0)
            y = coords.get("y", 0)
            w = coords.get("width", 0)
            h = coords.get("height", 0)
            font_size = coords.get("font_size") or coords.get("fontSize") or 12

            page = doc[page_index]
            rect = fitz.Rect(x, y, x + w, y + h)

            # 为该页面插入字体（每个页面只需插入一次）
            if page_index not in pages_with_font:
                try:
                    page.insert_font(fontfile=font_file_path, fontname="cjkfont")
                    pages_with_font.add(page_index)
                except Exception as e:
                    print(f"[export] 页面{page_index}字体插入失败: {e}")

            # 颜色设置
            stroke_color = fitz.utils.getColor("red")
            fill_color = fitz.utils.getColor("lightpink")

            page.draw_rect(rect, color=stroke_color, fill=fill_color, width=1)

            # 标注文本
            label = _get_field_label(ann.field_name)
            value = ann.field_value or ""

            # 使用正确的API：同时传入fontname和fontfile参数
            page.insert_text(
                fitz.Point(rect.x0 + 2, rect.y0 - 2),
                label,
                fontsize=font_size,
                color=stroke_color,
                fontname="cjkfont",
                fontfile=font_file_path
            )
            if value:
                page.insert_text(
                    fitz.Point(rect.x0 + 2, rect.y0 + font_size + 2),
                    value,
                    fontsize=font_size,
                    color=fitz.utils.getColor("black"),
                    fontname="cjkfont",
                    fontfile=font_file_path
                )

        doc.save(output_path)
        doc.close()
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出失败: {e}")

    download_name = f"{os.path.splitext(file.original_name)[0]}_annotated.pdf"
    return FileResponse(
        path=output_path,
        filename=download_name,
        media_type="application/pdf"
    )


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
            field_value=field.get("field_value", ""),
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
