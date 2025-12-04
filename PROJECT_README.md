# PDF 文档处理系统

一个集成了文档转换、PDF 编辑和文档标注的综合文档处理系统。

## 项目简介

本系统提供完整的 PDF 文档处理解决方案，包含以下核心功能：

### 核心功能模块

1. **文档转换模块**
   - 支持多种格式文件转换为 PDF（图片、Word、OFD等）
   - 支持压缩包批量处理（ZIP、RAR）
   - 智能识别文件类型，自动选择转换方案

2. **PDF 编辑模块**
   - 文本内容编辑
   - PDF 表单编辑
   - 注释和批注功能
   - 页面管理（增删、旋转、重排序）

3. **文档标注与信息抽取模块**
   - 可视化标注工具（文本、图片、表格标注）
   - 基于样本学习的智能信息抽取
   - 特别针对合同文档的关键字段识别
   - 标注结果的管理和导出

## 技术架构

### 后端技术栈
- **框架**: FastAPI 0.104+
- **语言**: Python 3.9+
- **数据库**: SQLite（可切换 PostgreSQL/MySQL）
- **PDF 处理**: PyMuPDF (fitz)、PyPDF2
- **文档转换**: python-docx、Pillow、img2pdf、pypandoc
- **压缩包**: zipfile、rarfile

### 前端技术栈
- **框架**: Vue 3
- **构建工具**: Vite
- **UI 组件库**: Element Plus
- **状态管理**: Pinia
- **路由**: Vue Router
- **HTTP 客户端**: Axios
- **Canvas 操作**: Fabric.js

## 项目结构

```
sanxia_demo/
├── backend/                  # 后端服务
│   ├── app/
│   │   ├── main.py          # FastAPI 入口
│   │   ├── config.py        # 配置管理
│   │   ├── database.py      # 数据库配置
│   │   ├── models/          # 数据模型
│   │   ├── schemas/         # Pydantic 模型
│   │   ├── api/             # API 路由
│   │   ├── services/        # 业务逻辑
│   │   └── utils/           # 工具函数
│   ├── uploads/             # 上传文件存储
│   ├── outputs/             # 处理结果存储
│   ├── temp/                # 临时文件
│   └── requirements.txt     # Python 依赖
│
├── frontend/                # 前端应用
│   ├── src/
│   │   ├── main.js         # 应用入口
│   │   ├── App.vue         # 根组件
│   │   ├── views/          # 页面组件
│   │   ├── components/     # 通用组件
│   │   ├── api/            # API 接口
│   │   ├── store/          # 状态管理
│   │   ├── router/         # 路由配置
│   │   └── utils/          # 工具函数
│   └── package.json        # npm 依赖
│
├── docs/                    # 项目文档
├── README.rd                # 需求文档
└── PROJECT_README.md        # 项目说明（本文件）
```

## 快速开始

### 环境要求

- Python 3.9+
- Node.js 16+
- npm 或 yarn

### 1. 安装后端依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置后端环境

复制并配置环境变量：

```bash
cd backend
cp .env.example .env
# 根据需要修改 .env 文件中的配置
```

### 3. 启动后端服务

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

后端服务将运行在：http://localhost:8000
API 文档地址：http://localhost:8000/docs

### 4. 安装前端依赖

```bash
cd frontend
npm install
```

### 5. 启动前端开发服务器

```bash
cd frontend
npm run dev
```

前端应用将运行在：http://localhost:5173

### 6. 访问应用

打开浏览器访问：http://localhost:5173

## 功能说明

### 文件上传
- 支持拖拽上传和点击上传
- 支持多文件同时上传
- 支持的格式：PDF, PNG, JPG, JPEG, DOC, DOCX, OFD, ZIP, RAR
- 单文件大小限制：50MB

### 文档转换
- 自动识别文件类型
- 支持批量转换
- 压缩包自动解压后转换
- 转换进度实时显示

### PDF 编辑
- **文本编辑**：修改、添加、删除 PDF 中的文本
- **表单编辑**：编辑 PDF 表单字段和值
- **注释批注**：添加高亮、下划线、文字注释
- **页面管理**：添加、删除、旋转、重排页面

### 文档标注
- **可视化标注**：通过界面直接标注关键信息
- **支持标注类型**：
  - 短文本标注
  - 长文本标注（多段落）
  - 图片标注
  - 表格标注
- **智能学习**：基于标注样本自动识别相似文档
- **合同处理**：专门优化的合同关键字段识别（名称、日期、编号、金额）
- **标注管理**：删除、修改、保存标注结果

## 开发路线图

### ✅ 已完成
- [x] 项目架构设计
- [x] 后端框架搭建（FastAPI）
- [x] 前端框架搭建（Vue 3 + Vite）
- [x] 基础页面和路由
- [x] 文件上传页面

### 🚧 进行中
- [ ] 文档转换模块实现
- [ ] PDF 编辑功能实现
- [ ] 文档标注功能实现

### 📋 计划中
- [ ] 用户认证和权限管理
- [ ] 批量处理优化
- [ ] 数据导出功能
- [ ] 性能优化和测试

## API 文档

后端 API 文档可通过 Swagger UI 访问：
http://localhost:8000/docs

主要 API 端点：

- `GET /` - 系统信息
- `GET /health` - 健康检查
- `POST /api/upload` - 文件上传
- `POST /api/convert/to-pdf` - 转换为 PDF
- `POST /api/edit/*` - PDF 编辑相关
- `POST /api/annotate/*` - 标注相关

## 部署说明

### 单机部署

1. **后端部署**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

2. **前端构建**
```bash
cd frontend
npm install
npm run build
```

3. **使用 Nginx 提供前端静态文件服务**

配置 Nginx 反向代理到后端服务。

### Docker 部署（可选）

TODO: 添加 Docker 配置文件

## 常见问题

### 1. 后端启动失败
- 检查 Python 版本是否 >= 3.9
- 检查是否正确安装了所有依赖
- 查看日志输出的具体错误信息

### 2. 前端连接后端失败
- 确认后端服务已启动
- 检查 vite.config.js 中的代理配置
- 检查防火墙设置

### 3. 文件上传失败
- 检查文件大小是否超过限制（50MB）
- 检查文件格式是否支持
- 查看后端日志中的错误信息

## 贡献指南

欢迎提交 Issue 和 Pull Request！

## 许可证

MIT License

## 联系方式

如有问题，请联系项目维护者。

---

**开发时间**: 2025年12月
**版本**: v1.0.0
