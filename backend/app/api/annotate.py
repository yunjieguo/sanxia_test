"""标注 API 路由"""
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File as FastAPIFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import json
import os
import uuid
import re
import textwrap
import logging

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
    ApplyTemplateLLMRequest,
    ApplyTemplateLLMResponse,
    PaintData
)
from ..config import settings
from ..services.ocr_engine import extract_text_blocks_with_fallback
from ..services.llm_client import DashScopeClient

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/annotations", tags=["标注管理"])
template_router = APIRouter(prefix="/api/templates", tags=["模板管理"])


def _extract_plain_text(file_path: str, max_len: int = 6000) -> str:
    """
    提取带页码的纯文本，用于 LLM 提示词。
    先尝试 PDF 文本层，无文本时会走 OCR 回退。
    """
    pages = extract_text_blocks_with_fallback(file_path) or []
    parts: List[str] = []
    for idx, blocks in enumerate(pages):
        texts = [b.get("text", "") for b in blocks if b.get("text")]
        if not texts:
            continue
        page_txt = f"[第{idx + 1}页]\n" + "\n".join(texts)
        parts.append(page_txt)
    content = "\n\n".join(parts)
    if len(content) > max_len:
        content = content[:max_len] + "\n...(截断)"
    return content


def _flatten_text_blocks(file_path: str, max_pages: int = 5, max_blocks: int = 200) -> List[Dict[str, Any]]:
    """将带坐标的文本块拍平成列表，供 LLM 选择。"""
    blocks_nested = extract_text_blocks_with_fallback(file_path)
    flat: List[Dict[str, Any]] = []
    for p_idx, page in enumerate(blocks_nested[:max_pages]):
        for b_idx, blk in enumerate(page or []):
            text = (blk.get("text") or "").strip()
            bbox = blk.get("bbox")
            if not text or not bbox or len(bbox) != 4:
                continue
            flat.append({
                "id": f"p{p_idx+1}_b{b_idx+1}",
                "page": p_idx + 1,
                "bbox": [float(b) for b in bbox],
                "text": text[:120]  # 避免过长
            })
            if len(flat) >= max_blocks:
                return flat
    return flat


def _call_llm_extract_fields(template: Template, file: File, blocks: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    调用 DashScope/Qwen（多模态）做字段抽取。
    返回 {field_name: {value, page_number}}，未识别的字段不在结果中。
    如果未配置 API KEY，会抛异常，让上层回退。
    """
    if not settings.DASHSCOPE_API_KEY:
        raise RuntimeError("未配置 DASHSCOPE_API_KEY")

    client = DashScopeClient(
        api_key=settings.DASHSCOPE_API_KEY,
        endpoint=settings.DASHSCOPE_ENDPOINT,
        model_name=settings.QWEN_MODEL_NAME or "qwen-vl-max"
    )

    # 解析模板字段定义（模板存储为 JSON 字符串时先反序列化）
    tpl_data = template.template_data
    if isinstance(tpl_data, str):
        try:
            tpl_data = json.loads(tpl_data)
        except Exception:
            tpl_data = {}
    if not isinstance(tpl_data, dict):
        tpl_data = {}

    template_fields = []
    if tpl_data.get("fields"):
        for f in tpl_data.get("fields", []):
            template_fields.append({
                "field_name": f.get("field_name"),
                "field_type": f.get("field_type", "text")
            })
    else:
        template_fields.append({"field_name": "contract_name", "field_type": "text"})

    plain_text = _extract_plain_text(file.file_path)
    blocks_text = json.dumps(blocks, ensure_ascii=False)
    prompt = textwrap.dedent(f"""
    你是文档抽取助手。请根据提供的带坐标文本块，抽取指定字段，给出值、页码和对应的 bbox。
    字段列表：{template_fields}
    文本块列表（含 bbox 与 page）：{blocks_text}
    规则：
    1) 仅从给定文本块中选择最匹配的块，返回其 bbox（[x0,y0,x1,y1]）与页码。
    2) 输出 JSON，格式：{{"fields":[{{"field_name":"...","value":"...","page_number":1,"bbox":[x0,y0,x1,y1],"confidence":0.9}}...]}}
    3) 若未找到可返回空字符串，但请保持 JSON 结构。
    """).strip()

    messages = [
        {"role": "system", "content": "You are a helpful assistant for document information extraction. Respond in JSON only."},
        {"role": "user", "content": prompt}
    ]
    data = client.generate(messages)

    # 解析返回的 JSON 片段，兼容多种返回结构
    content = ""
    if isinstance(data, str):
        content = data
    else:
        try:
            output = data.get("output") if hasattr(data, "get") else None
            # 只在 output 是字典时再取 choices
            choices = None
            if isinstance(output, dict):
                choices = output.get("choices")
            # 顶层 choices 兜底
            if choices is None and hasattr(data, "get"):
                choices = data.get("choices")
            if choices:
                first = choices[0]
                if isinstance(first, str):
                    content = first
                elif isinstance(first, dict):
                    content = first.get("message", {}).get("content", "") or first.get("content", "")
            # 兼容 output_text 或 output 为字符串/列表
            if not content:
                if isinstance(output, str):
                    content = output
                elif isinstance(output, list):
                    content = json.dumps(output, ensure_ascii=False)
                elif hasattr(data, "get"):
                    ot = data.get("output_text")
                    if isinstance(ot, list):
                        content = json.dumps(ot, ensure_ascii=False)
                    else:
                        content = ot or ""
        except Exception:
            content = ""

    if not content:
        raise RuntimeError("LLM 无返回内容")

    json_str = ""
    # 优先提取代码块内 JSON
    if not isinstance(content, str):
        content = json.dumps(content, ensure_ascii=False)

    code_blocks = re.findall(r"```(?:json)?\s*(\{.*?\})\s*```", content, flags=re.S)
    if code_blocks:
        json_str = code_blocks[0]
    else:
        # 回退：直接找第一个 { 开始的 JSON
        m = re.search(r"\{.*\}", content, flags=re.S)
        if m:
            json_str = m.group(0)
    if not json_str:
        raise RuntimeError(f"无法解析 LLM 返回: {content[:200]}")

    parsed = json.loads(json_str)
    if not isinstance(parsed, dict):
        raise RuntimeError(f"LLM 返回非对象结构: {type(parsed).__name__}")

    fields = parsed.get("fields") or []
    result: Dict[str, Dict[str, Any]] = {}
    for f in fields:
        name = f.get("field_name")
        val = f.get("value")
        if not name or val is None:
            continue
        bbox = f.get("bbox")
        coords = None
        if isinstance(bbox, (list, tuple)) and len(bbox) == 4:
            coords = {
                "x": float(bbox[0]),
                "y": float(bbox[1]),
                "width": float(bbox[2]) - float(bbox[0]),
                "height": float(bbox[3]) - float(bbox[1]),
            }
        result[name] = {
            "value": val,
            "page_number": f.get("page_number"),
            "bbox": bbox if isinstance(bbox, (list, tuple)) else None,
            "coords": coords,
            "confidence": f.get("confidence")
        }
    return result


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
    use_matching: bool = False,
    llm_results: Optional[Dict[str, Dict[str, Any]]] = None
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

    # 预置字段关键词
    preset_keywords = {
        "contract_name": ["合同名称", "合同书", "合同名称：", "合同题目"],
        "contract_date": ["合同日期", "签订日期", "签署日期", "签约日期"],
        "contract_number": ["合同编号", "合同号", "编号", "编号："],
        "contract_amount": ["合同金额", "总金额", "金额", "价款", "人民币", "价款总额"],
        "party_a": ["甲方", "甲方名称", "需方", "购买方"],
        "party_b": ["乙方", "乙方名称", "供方", "销售方"]
    }
    date_pattern = re.compile(r"\d{4}[./-年]?\s*\d{1,2}[./-月]?\s*\d{1,2}[日号]?")
    number_pattern = re.compile(r"(合同编号[:：]?\s*[A-Za-z0-9\\-_/]+)")
    amount_pattern = re.compile(r"[¥￥]?\s*\d[\\d,\\.]*\\s*元?")
    party_pattern = re.compile(r"(甲方|乙方)[:：]\s*([\u4e00-\u9fa5A-Za-z0-9()（）·\s]+)")

    def _looks_like_amount(text: str) -> bool:
        t = (text or "").strip()
        if not t:
            return False
        # 含货币符号/单位
        if ("¥" in t or "￥" in t or "元" in t or "人民币" in t or "万" in t) and re.search(r"\d", t):
            return True
        # 纯数字金额：含小数点或逗号，且不含日期分隔符
        if any(ch in t for ch in [".", ","]) and not any(sep in t for sep in ["年", "月", "-", "/"]):
            return re.search(r"\d", t) is not None
        return False

    def _strict_date_match(text: str):
        """更严格的日期匹配，校验年月日范围，避免 30000.00 被误判。"""
        if not text:
            return None
        t = text.strip()
        # 必须包含日期分隔符或年月
        if not any(sep in t for sep in ["年", "月", "-", "/"]):
            return None
        # 统一分隔符
        tmp = re.sub(r"[年/.]", "-", t)
        m = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", tmp)
        if not m:
            return None
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if not (1 <= mo <= 12 and 1 <= d <= 31):
            return None
        return m.group(0)

    def _looks_like_date(text: str) -> bool:
        return _strict_date_match(text) is not None

    def _is_expected_party(field_name: str, text: str) -> bool:
        """严格区分甲/乙方，避免互相误标。"""
        t = text or ""
        if field_name == "party_a":
            return "甲方" in t or "需方" in t or "购买方" in t
        if field_name == "party_b":
            return "乙方" in t or "供方" in t or "销售方" in t
        return True

    def _extract_value_after_keyword(text: str, keyword: str) -> str:
        """从命中文本中提取关键词后的内容，例如 '甲方：某某公司'。"""
        if not text:
            return ""
        parts = re.split(r"[:：]", text, maxsplit=1)
        if len(parts) == 2:
            right = parts[1].strip()
            # 去掉再次出现的关键词
            if keyword and right.startswith(keyword):
                right = right[len(keyword):].lstrip("：:").strip()
            return right or text.strip()
        return text.strip()

    POINTS_TO_PX = 96.0 / 72.0  # fitz 返回 point，前端 pdf.js 默认 96dpi

    def _scale_coords(c: Dict[str, float]) -> Dict[str, float]:
        return {
            "x": c.get("x", 0) * POINTS_TO_PX,
            "y": c.get("y", 0) * POINTS_TO_PX,
            "width": c.get("width", 0) * POINTS_TO_PX,
            "height": c.get("height", 0) * POINTS_TO_PX,
            "font_size": c.get("font_size"),
            "font_color": c.get("font_color"),
            "font_family": c.get("font_family")
        }

    def _match_field(field_def):
        """
        返回同一字段的全部命中 [(coords, page, conf, strategy, note, value), ...]
        """
        # 默认坐标
        coords = field_def.get("coordinates") or {
            "x": base_x,
            "y": base_y,
            "width": 180,
            "height": 36
        }
        page_number = field_def.get("page_number") or 1
        confidence = field_def.get("confidence_threshold") or 0.3
        note = "未找到匹配，使用模板坐标"
        field_value = None

        # 如果有 LLM 结果，优先使用 LLM 返回的坐标/值（单个返回），并做字段校验
        if llm_results and field_def.get("field_name") in llm_results:
            llm_item = llm_results[field_def.get("field_name")]
            llm_coords = llm_item.get("coords")
            llm_page = llm_item.get("page_number") or page_number
            llm_value = llm_item.get("value") or field_value
            llm_conf = llm_item.get("confidence") or 0.9
            # 甲/乙方严格校验
            if field_def.get("field_name") in ("party_a", "party_b") and llm_value:
                if not _is_expected_party(field_def.get("field_name"), str(llm_value)):
                    llm_coords = None  # 丢弃不符合的 LLM 结果
            if llm_coords and llm_page:
                logger.info(f"[LLM] {field_def.get('field_name')} page={llm_page} conf={llm_conf} value={llm_value}")
                return [(_scale_coords(llm_coords), llm_page, llm_conf, "llm", "LLM 返回坐标", llm_value)]

        if not use_matching or not text_blocks:
            logger.info(f"[MATCH] {field_def.get('field_name')} 未开启匹配，使用模板坐标 page={page_number}")
            return [(coords, page_number, confidence, "template_coordinates", note, field_value)]

        field_name = field_def.get("field_name", "")
        keywords = field_def.get("keywords") or preset_keywords.get(field_name, []) or [field_name]
        keywords = [kw for kw in keywords if kw]
        anchor_offset = field_def.get("anchor_offset") or {}
        off_x = anchor_offset.get("x", 0)
        off_y = anchor_offset.get("y", 0)

        # 不再按模板页码限制，始终遍历新文档的所有页
        target_pages = list(range(len(text_blocks)))

        found_hits = []

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
                raw_text = (blk.get("text") or "").strip()
                text_lower = raw_text.lower()
                hit_kw = None
                for kw in keywords:
                    if kw.lower() in text_lower:
                        hit_kw = kw
                        break
                if hit_kw:
                    bbox = blk["bbox"]
                    width = coords.get("width") or (bbox[2] - bbox[0])
                    height = coords.get("height") or (bbox[3] - bbox[1])

                    # 尝试合并同一行的下一个文本块，避免“甲方：”与公司名分离
                    merged_bbox = [bbox[0], bbox[1], bbox[2], bbox[3]]
                    merged_text = raw_text
                    if blk_idx + 1 < len(page_blocks):
                        nxt = page_blocks[blk_idx + 1]
                        nbbox = nxt.get("bbox")
                        ntext = (nxt.get("text") or "").strip()
                        if nbbox and ntext:
                            same_line = abs((nbbox[1] + nbbox[3]) / 2 - (bbox[1] + bbox[3]) / 2) < max(height, nbbox[3] - nbbox[1]) * 0.6
                            if same_line:
                                merged_text = (raw_text + " " + ntext).strip()
                                merged_bbox[2] = max(merged_bbox[2], nbbox[2])
                                merged_bbox[3] = max(merged_bbox[3], nbbox[3])
                                width = coords.get("width") or (merged_bbox[2] - merged_bbox[0])
                                height = coords.get("height") or (merged_bbox[3] - merged_bbox[1])

                    found = {
                        "x": merged_bbox[0] + off_x,
                        "y": merged_bbox[1] + off_y,
                        "width": width,
                        "height": height,
                        "page_number": p_idx + 1,
                        "keyword": hit_kw
                    }

                    # 提取字段值：短文本取合并后的文本，长文本尝试多行
                    ftype = field_def.get("field_type")
                    if ftype == "long_text":
                        long_cfg = field_def.get("long_text") or {}
                        field_value = _gather_long_text(page_blocks, blk_idx, long_cfg) or merged_text
                    elif ftype == "text":
                        # 尝试提取冒号后的值
                        field_value = _extract_value_after_keyword(merged_text, hit_kw)
                    else:
                        field_value = field_def.get("field_value")
                    # 甲/乙方严格校验
                    if field_name in ("party_a", "party_b") and not _is_expected_party(field_name, merged_text):
                        continue
                    found_hits.append((found, field_value))
                    continue
                # 关键词未命中，尝试正则抽取特定字段
                if not hit_kw and field_name:
                    if field_name == "contract_date":
                        # 避免金额误判成日期，使用严格日期匹配
                        if _looks_like_amount(raw_text):
                            m = None
                        else:
                            strict_val = _strict_date_match(raw_text)
                            m = None
                            if strict_val:
                                m = re.search(re.escape(strict_val), raw_text)
                        if m:
                            found = {
                                "x": blk["bbox"][0] + off_x,
                                "y": blk["bbox"][1] + off_y,
                                "width": coords.get("width") or (blk["bbox"][2] - blk["bbox"][0]),
                                "height": coords.get("height") or (blk["bbox"][3] - blk["bbox"][1]),
                                "page_number": p_idx + 1,
                                "keyword": "regex_date"
                            }
                            field_value = m.group(0).strip()
                            found_hits.append((found, field_value))
                            continue
                    elif field_name == "contract_number":
                        m = number_pattern.search(raw_text)
                        if m:
                            found = {
                                "x": blk["bbox"][0] + off_x,
                                "y": blk["bbox"][1] + off_y,
                                "width": coords.get("width") or (blk["bbox"][2] - blk["bbox"][0]),
                                "height": coords.get("height") or (blk["bbox"][3] - blk["bbox"][1]),
                                "page_number": p_idx + 1,
                                "keyword": "regex_number"
                            }
                            field_value = m.group(0).replace("合同编号", "").replace("编号", "").replace("：", "").replace(":", "").strip()
                            found_hits.append((found, field_value))
                            continue
                    elif field_name == "contract_amount":
                        # 避免日期误判成金额
                        if _looks_like_date(raw_text):
                            m = None
                        else:
                            m = amount_pattern.search(raw_text)
                        if m:
                            found = {
                                "x": blk["bbox"][0] + off_x,
                                "y": blk["bbox"][1] + off_y,
                                "width": coords.get("width") or (blk["bbox"][2] - blk["bbox"][0]),
                                "height": coords.get("height") or (blk["bbox"][3] - blk["bbox"][1]),
                                "page_number": p_idx + 1,
                                "keyword": "regex_amount"
                            }
                            field_value = m.group(0).strip()
                            found_hits.append((found, field_value))
                            continue
                    elif field_name in ("party_a", "party_b"):
                        m = party_pattern.search(raw_text)
                        if m:
                            prefix = m.group(1)
                            val = m.group(2).strip()
                            if (field_name == "party_a" and prefix == "甲方") or (field_name == "party_b" and prefix == "乙方"):
                                found = {
                                    "x": blk["bbox"][0] + off_x,
                                    "y": blk["bbox"][1] + off_y,
                                    "width": coords.get("width") or (blk["bbox"][2] - blk["bbox"][0]),
                                    "height": coords.get("height") or (blk["bbox"][3] - blk["bbox"][1]),
                                    "page_number": p_idx + 1,
                                    "keyword": "regex_party"
                                }
                                field_value = val
                                found_hits.append((found, field_value))
                            continue
            # 不再 break，允许同字段多页多次命中

        if found_hits:
            results = []
            for fnd, fval in found_hits:
                results.append(
                    (
                        _scale_coords({
                            "x": fnd["x"],
                            "y": fnd["y"],
                            "width": fnd["width"],
                            "height": fnd["height"],
                            "font_size": coords.get("font_size"),
                            "font_color": coords.get("font_color"),
                            "font_family": coords.get("font_family")
                        }),
                        fnd["page_number"],
                        max(confidence, 0.8),
                        "regex" if fnd.get("keyword", "").startswith("regex") else "keyword_offset",
                        f"命中关键词: {fnd.get('keyword')}" if fnd.get("keyword") else "正则匹配",
                        fval
                    )
                )
                logger.info(f"[MATCH] {field_def.get('field_name')} hit page={fnd['page_number']} strategy={'regex' if fnd.get('keyword','').startswith('regex') else 'keyword'} value={fval}")
            return results

        # 如果启用了匹配但未命中：
        # 对甲/乙方不回退，避免无内容时仍落模板页；其他字段仍可回退模板坐标
        if use_matching:
            if field_name in ("party_a", "party_b"):
                logger.info(f"[MATCH] {field_name} 未命中，跳过回退模板坐标")
                return []
            return [(coords, page_number, confidence, "template_coordinates", "未命中，回退模板坐标", field_value)]

        # 未启用匹配时才回退模板坐标
        return [(coords, page_number, confidence, "template_coordinates", note, field_value)]

    for idx, field in enumerate(fields):
        field_name = field.get("field_name", f"field_{idx+1}")

        coords_default = field.get("coordinates") or {
            "x": base_x,
            "y": base_y + idx * gap_y,
            "width": 180,
            "height": 36
        }
        page_default = field.get("page_number") or 1

        # 匹配可能返回多条
        if use_matching:
            matches = _match_field(field)
        else:
            matches = [(coords_default, page_default, 0.3, "template_coordinates", "未启用匹配", None)]

        for coords, match_page, match_conf, strategy, note, matched_value in matches:
            ann = Annotation(
                file_id=file.id,
                page_number=match_page,
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
                    "page_number": match_page,
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


@template_router.post("/{template_id}/apply-llm", response_model=ApplyTemplateResponse, summary="LLM 一键应用模板")
async def apply_template_llm(
    template_id: int,
    request: ApplyTemplateLLMRequest,
    db: Session = Depends(get_db)
):
    """
    调用大模型抽取字段并回填标注：
    1) 若配置了 DASHSCOPE_API_KEY，则调用 LLM 获取字段值；定位仍复用匹配/模板坐标。
    2) 若未配置或调用失败，则回退到匹配逻辑。
    """
    # 兼容 body 未带 template_id 的情况
    if request.template_id and request.template_id != template_id:
        template_id = request.template_id

    template = db.query(Template).filter(Template.id == template_id).first()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    file = db.query(File).filter(File.id == request.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="文件不存在")

    llm_fields: Dict[str, Dict[str, Any]] = {}
    llm_notes: List[Dict[str, Any]] = []
    llm_used = False

    try:
        blocks = _flatten_text_blocks(file.file_path)
        llm_fields = _call_llm_extract_fields(template, file, blocks)
        llm_used = True
    except Exception as e:
        # 未配置或调用异常，走回退
        llm_notes.append({"note": f"LLM 回退: {e}"})

    # 基础定位仍走匹配/模板坐标
    resp = _apply_template_to_file(template, file, db, use_matching=True)

    # 如果有 LLM 结果，填充字段值并标记策略
    if llm_used and resp.extracted_data:
        for item in resp.extracted_data:
            if item["field_name"] in llm_fields:
                item["field_value"] = llm_fields[item["field_name"]].get("value", item["field_value"])
        # 增补 match_details 说明 LLM 参与
        details = resp.match_details or []
        for name, info in llm_fields.items():
            details.append({
                "field_name": name,
                "page_number": info.get("page_number"),
                "strategy": "llm",
                "confidence": None,
                "note": "LLM 抽取字段值"
            })
        details.extend(llm_notes)
        resp.match_details = details

    if llm_notes and not llm_used:
        resp.message = f"{resp.message or '已回退匹配逻辑'}（LLM 未调用: {llm_notes[0]['note']}）"
    else:
        resp.message = resp.message or "LLM 一键应用完成"
    return resp


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
