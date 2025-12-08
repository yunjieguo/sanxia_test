# PDF 转换 & 文档标注说明

## 功能概览
- PDF 转换：支持 Word/图片/压缩包/OFD 转 PDF，多文件上传，状态查询，结果存储在 backend/outputs/。
- 文档标注：前端 Canvas 标注与模板管理；后端 FastAPI + SQLAlchemy；关键词/页码提示/锚点偏移匹配；OCR 回退（PaddleOCR）；LLM 一键应用（通义 qwen-vl 系列）。

## 技术栈
- 前端：Vue3 + Vite + Element Plus
- 后端：Python + FastAPI + SQLAlchemy
- OCR：PyMuPDF 文本块 + PaddleOCR 回退（需 Python3.10 环境）
- LLM：通义 DashScope（默认 qwen-vl-max），接口 /api/templates/{id}/apply-llm

## 快速启动
后端
`ash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
`

前端
`ash
cd frontend
npm install
npm run dev
`

## 配置
- backend/.env 关键项：DASHSCOPE_API_KEY、DASHSCOPE_ENDPOINT、QWEN_MODEL_NAME、ENABLE_OCR、OCR_PROVIDER、UPLOAD_DIR 等。
- LLM 调用：POST /api/templates/{id}/apply-llm，前端模板列表提供“LLM 一键应用”按钮（可配置 top_k、image_width）。

## 说明
- 项目已移除 PDF 编辑功能，保留转换与标注。
