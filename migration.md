# 一、依赖环境及启动方式

依赖环境
```
安装 Python（与当前一致，建议 3.10/3.11/3.12 之一）。
安装 Node.js（与你前端构建时版本相近，如 18/20）。
安装 Git。
如需 OCR/LLM，确保能访问依赖（如 paddleocr 的包、DashScope 网络等）。
```

前端依赖与构建/运行
```bash
cd ../frontend
npm install
npm run dev   # 开发模式，默认 5173
# 或 npm run build && npm run preview 进行预览/生产构建
```

启动后端
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

# 二、迁移到内网/无网络环境的操作指引
1) 准备代码与数据
- 拷贝整个仓库目录（包含 backend/app.db，如需迁移已有标注/文件，则连同上传目录 settings.UPLOAD_DIR 指向的路径一起打包）。
- 复制或重新创建 backend/.env，保持与现有环境一致（数据库路径、DASHSCOPE_API_KEY 等）。

2) 后端 Python 依赖离线包
在有网机器（项目根目录）：
```bash
pip install -r backend/requirements.txt
pip download -r backend/requirements.txt -d offline_packages
```
将 offline_packages 目录拷贝到内网机器后：
```bash
pip install --no-index --find-links=offline_packages -r backend/requirements.txt
```

3) 前端依赖离线处理
方案 A（简单）：直接拷贝前端已安装的 node_modules（体积较大，适合一次性迁移）。
方案 B（缓存）：在有网机器执行
```bash
cd frontend
npm install
npm config set cache ../npm-offline-cache
```
打包 frontend 目录和 npm-offline-cache 目录。在内网机器：
```bash
cd frontend
npm config set cache ../npm-offline-cache
npm ci --offline   # 依赖已在缓存中
```
如果离线编译不便，可在有网机器先 `npm run build`，将前端 `dist` 目录打包，内网仅托管静态文件（如 npm run preview 或 Nginx）。

4) 启动后端
```bash
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000
```
确保 settings.UPLOAD_DIR 指向的目录存在且可写。

5) OCR/LLM 注意
- PaddleOCR 等依赖已在 offline_packages 中；如需 GPU/VC 运行库，提前在内网机器安装。
- DashScope/Qwen 等在线大模型在无网环境不可用，相关功能会回退；若需离线大模型，需另行部署本地推理服务并替换当前调用。

6) 验证
- 前端：若有 dist，可直接预览或托管；否则在缓存可用情况下 `npm run dev`。
- 接口自测：`GET http://localhost:8000/api/templates`、`GET http://localhost:8000/api/files`。
- 上传/标注目录写权限确认。
