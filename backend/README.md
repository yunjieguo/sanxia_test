# PDF 文档处理系统 - 后端

基于 FastAPI 的 PDF 文档处理后端服务。

## 功能模块

- 📄 文档转换：支持多种格式转 PDF
- ✏️ ：文本编辑、表单编辑、注释批注、页面管理
- 🏷️ 文档标注：可视化标注和信息自动抽取

## 技术栈

- FastAPI 0.104+
- Python 3.9+
- SQLite/PostgreSQL
- PyMuPDF (PDF 处理)
- SQLAlchemy (ORM)

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并修改配置：

```bash
cp .env.example .env
```

### 3. 启动服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

或者使用 Python 直接运行：

```bash
python -m uvicorn app.main:app --reload
```

### 4. 访问 API 文档

启动后访问：http://localhost:8000/docs

## 项目结构

```
backend/
├── app/
│   ├── main.py              # 应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库配置
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic 模型
│   ├── api/                 # API 路由
│   ├── services/            # 业务逻辑
│   └── utils/               # 工具函数
├── uploads/                 # 上传文件
├── outputs/                 # 输出文件
├── temp/                    # 临时文件
└── requirements.txt         # Python 依赖
```

## API 接口

### 文件上传
- `POST /api/upload` - 上传文件

### 文档转换
- `POST /api/convert/to-pdf` - 转换为 PDF
- `GET /api/convert/status/{task_id}` - 查询转换状态

### 
- `POST /api/edit/text` - 编辑文本
- `POST /api/edit/form` - 编辑表单
- `POST /api/edit/annotation` - 添加注释
- `POST /api/edit/page` - 页面管理

### 文档标注
- `POST /api/annotate/create` - 创建标注
- `POST /api/annotate/extract` - 信息抽取
- `GET /api/annotate/templates` - 获取模板列表

## 开发说明

### 添加新的 API 路由

1. 在 `app/api/` 目录下创建新的路由文件
2. 在 `app/main.py` 中导入并注册路由

### 添加新的服务

1. 在 `app/services/` 目录下创建服务文件
2. 在路由中调用服务方法

## 注意事项

- 上传文件大小限制：50MB
- 支持的文件格式：pdf, png, jpg, jpeg, doc, docx, ofd, zip, rar
- 临时文件会定期清理
