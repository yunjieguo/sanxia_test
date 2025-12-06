"""OCR/布局解析引擎占位实现。

优先使用 PDF 文本层；如启用并安装 PaddleOCR，则可对无文字页进行 OCR。
预留 LayoutLMv3 模型名称配置，但此处不直接加载大模型，只负责提供文本+坐标。
"""
from typing import List, Dict, Any, Optional
import os

from ..config import settings


def _try_import_paddle():
    try:
        from paddleocr import PaddleOCR  # type: ignore
    except Exception as e:
        raise ImportError(f"PaddleOCR 未安装或加载失败: {e}")
    return PaddleOCR


class LayoutAwareOCREngine:
    """提供文本+坐标的抽取接口，若未安装 OCR 依赖则优雅降级为空结果。"""

    _paddle_instance: Optional[Any] = None

    @classmethod
    def _get_paddle(cls):
        if cls._paddle_instance:
            return cls._paddle_instance
        PaddleOCR = _try_import_paddle()
        cls._paddle_instance = PaddleOCR(
            use_angle_cls=True,
            lang="ch",
            use_gpu=settings.OCR_USE_GPU
        )
        return cls._paddle_instance

    @classmethod
    def extract_layout(cls, file_path: str) -> List[List[Dict[str, Any]]]:
        """
        返回结构：List[page]，每页为若干 block: {"bbox": (x0,y0,x1,y1), "text": str}
        仅在 settings.ENABLE_OCR 为 True 时尝试 OCR，否则返回空列表。
        """
        if not settings.ENABLE_OCR:
            return []
        if not os.path.exists(file_path):
            return []

        try:
            ocr = cls._get_paddle()
        except Exception as e:
            print(f"OCR 未启用或加载失败，跳过 OCR: {e}")
            return []

        try:
            # PaddleOCR 对 PDF 会逐页处理；这里简单处理前 N 页（示例全部）
            result = ocr.ocr(file_path, cls=True)
        except Exception as e:
            print(f"OCR 识别失败: {e}")
            return []

        pages: List[List[Dict[str, Any]]] = []
        for page_res in result or []:
            blocks = []
            for line in page_res:
                if not line or len(line) < 2:
                    continue
                bbox = line[0]
                text = line[1][0] if line[1] else ""
                if not text:
                    continue
                x0 = min([p[0] for p in bbox])
                y0 = min([p[1] for p in bbox])
                x1 = max([p[0] for p in bbox])
                y1 = max([p[1] for p in bbox])
                blocks.append({"bbox": (x0, y0, x1, y1), "text": text})
            pages.append(blocks)
        return pages


def extract_text_blocks_with_fallback(file_path: str) -> List[List[Dict[str, Any]]]:
    """
    封装函数：先尝试用 PyMuPDF（文本层），若无文本且开启 OCR，则用 PaddleOCR。
    """
    text_blocks: List[List[Dict[str, Any]]] = []
    try:
        import fitz

        doc = fitz.open(file_path)
        for page_index in range(doc.page_count):
            page = doc.load_page(page_index)
            blocks = page.get_text("blocks") or []
            page_blocks = []
            for blk in blocks:
                if len(blk) >= 5 and isinstance(blk[4], str) and blk[4].strip():
                    page_blocks.append({"bbox": (blk[0], blk[1], blk[2], blk[3]), "text": blk[4]})
            text_blocks.append(page_blocks)
        doc.close()
    except Exception as e:
        print(f"读取 PDF 文本失败: {e}")
        text_blocks = []

    # 如果已有文本层则直接返回
    has_text = any(page for page in text_blocks)
    if has_text:
        return text_blocks

    # 退回 OCR
    ocr_blocks = LayoutAwareOCREngine.extract_layout(file_path)
    return ocr_blocks
