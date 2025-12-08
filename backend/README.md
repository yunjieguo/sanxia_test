# PDF 处理系统 - 后端

## 功能
- PDF 转换：Word/图片/压缩包/OFD 转 PDF。
- 文档标注：模板保存/应用，关键词+位置匹配，OCR 回退（PaddleOCR），LLM 一键应用（通义 qwen-vl 系列）。

## 技术栈
- FastAPI + SQLAlchemy
- PyMuPDF、Pillow、img2pdf、python-docx
- PaddleOCR（需 Python3.10）
- DashScope 通义多模态（默认 qwen-vl-max）

## 启动
`ash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
`

## 配置（.env 关键项）
- DATABASE_URL
- UPLOAD_DIR / OUTPUT_DIR / TEMP_DIR
- ENABLE_OCR, OCR_PROVIDER, OCR_USE_GPU
- DASHSCOPE_API_KEY, DASHSCOPE_ENDPOINT, QWEN_MODEL_NAME
