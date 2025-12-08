# TODO

## PDF 转换
- 技术栈：FastAPI + SQLAlchemy（任务记录）；PyMuPDF/PyPDF2 读取；Pillow 处理图片转 PDF；img2pdf、python-docx、zip 解包复用；前端 Vue3 + Vite + Element Plus。
- 状态：Word/图片/压缩包/OFD 转 PDF 已跑通；支持多文件上传与状态查询；输出保存到 `backend/outputs/`。
- 后续：补充失败重试与并发队列；对大文件/多页做流式处理与进度提示；完善格式兼容性（含字体嵌入）。

## PDF 文档标注
- 技术栈：前端 Canvas/Element Plus，后端 FastAPI + SQLAlchemy；PyMuPDF 文本块，PaddleOCR 作为无文本页回退（`.env` 中 `ENABLE_OCR`, `OCR_PROVIDER`, `OCR_USE_GPU` 控制）；模板字段支持关键词、页码提示、锚点偏移、长文本/图片/表格元数据。
- 状态：标注创建/更新/批量接口可用；模板保存/应用可用；一键应用支持关键词+位置匹配并返回置信度；OCR 回退已接入 PaddleOCR（需 Python3.10 环境）。
- LLM 模式：新增后端 `/api/templates/{id}/apply-llm`，调用通义 `qwen-vl-max`（DashScope），按模板+页面截图返回 bbox/置信度并入库；前端模板列表增加“LLM 一键应用”按钮，带全局 loading。
- 待办：前端补进度/失败提示和参数配置（top_k、image_width）；表格/长文本跨页的标注与回显优化；OCR 结果缓存落库；集成 LayoutLMv3 做模板迁移；修复 README 乱码并补充 LLM/OCR 使用说明；测试与性能脚本。
