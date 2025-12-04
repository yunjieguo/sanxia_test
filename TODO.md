# PDF 文档处理系统 - 开发任务清单

> 本文档记录所有待开发功能和开发进度
>
> **项目状态：** 文档转换模块已完成，文档标注模块待开发
>
> **总体完成度：** 约 35%（基础架构 + 文件上传 + 文档转换）
>
> **最后更新：** 2025-12-04

---

## 📊 项目概览

### 当前状态

#### ✅ 已完成的基础设施

- ✅ 前后端项目架构搭建
- ✅ FastAPI 后端框架配置
- ✅ Vue 3 + Vite 前端框架配置
- ✅ Element Plus UI 组件库集成
- ✅ 数据库配置（SQLite）
- ✅ CORS 跨域配置
- ✅ 静态文件服务配置
- ✅ 首页导航界面
- ✅ 文件上传页面 UI（仅前端，无后端支持）
- ✅ 路由配置（5个页面）
- ✅ Axios 请求封装
- ✅ Pinia 状态管理基础

#### ✅ 已完成的核心功能

1. **文档转换模块（100%）**
   - ✅ 图片转 PDF（PNG, JPG, JPEG, GIF, BMP）
   - ✅ Word 文档转 PDF（DOC, DOCX）
   - ✅ OFD 转 PDF
   - ✅ 压缩包批量转换（ZIP, RAR）
   - ✅ 转换进度显示
   - ✅ 文件下载功能

#### ❌ 待开发的核心功能

**两大核心模块待实现：**
1. PDF 编辑模块（0%）
2. 文档标注与信息抽取模块（0%）

---

## 🎯 开发路线图

### 第一阶段：基础功能（优先级最高）

#### 1.1 文件上传功能 ✅ 已完成

**目标：** 实现完整的文件上传和存储功能

**后端任务：**
- ✅ 创建 `backend/app/models/file.py` - 文件记录数据模型 ✅
  - 字段：id, filename, original_name, file_type, file_size, file_path, upload_time, status
- ✅ 创建 `backend/app/schemas/file.py` - 文件相关 Pydantic Schema ✅
  - FileUploadResponse
  - FileInfoResponse
  - FileListResponse
- ✅ 创建 `backend/app/services/file_handler.py` - 文件处理服务 ✅
  - `save_upload_file()` - 保存上传文件
  - `validate_file_type()` - 文件类型验证
  - `validate_file_size()` - 文件大小验证（50MB 限制）
  - `generate_safe_filename()` - 生成安全文件名
  - `get_file_info()` - 获取文件信息
  - `delete_file()` - 删除文件
- ✅ 创建 `backend/app/api/upload.py` - 文件上传 API 路由 ✅
  - `POST /api/upload` - 上传文件接口
  - `GET /api/files` - 获取文件列表
  - `GET /api/files/{file_id}` - 获取文件详情
  - `DELETE /api/files/{file_id}` - 删除文件
- ✅ 在 `backend/app/main.py` 中注册上传路由 ✅
- ✅ 创建数据库迁移脚本（使用自动创建表）✅

**前端任务：**
- ✅ 创建 `frontend/src/api/upload.js` - 上传 API 封装 ✅
  - `uploadFile()` - 上传文件
  - `getFileList()` - 获取文件列表
  - `getFileInfo()` - 获取文件详情
  - `deleteFile()` - 删除文件
- ✅ 修改 `frontend/src/views/Upload.vue` - 对接后端 API ✅
  - 集成上传 API
  - 显示上传进度
  - 显示上传结果
  - 文件列表展示
- ✅ 修复 API 路径问题（/api/api/ → /api/）✅
- ✅ 修复 Upload 图标导入问题 ✅

**测试验证：**
- [ ] 测试单文件上传
- [ ] 测试多文件上传
- [ ] 测试文件类型验证
- [ ] 测试文件大小限制
- [ ] 测试文件列表显示
- [ ] 测试文件删除功能

---

#### 1.2 数据库模型设计 ✅ 部分完成

**目标：** 建立完整的数据库表结构

**任务清单：**
- ✅ 创建 `backend/app/models/file.py` - 文件表 ✅
  ```python
  - id: 主键
  - filename: 存储文件名
  - original_name: 原始文件名
  - file_type: 文件类型（pdf/png/jpg/doc等）
  - file_size: 文件大小（字节）
  - file_path: 文件存储路径
  - upload_time: 上传时间
  - status: 文件状态（uploaded/converting/converted/failed）
  - created_at: 创建时间
  - updated_at: 更新时间
  ```

- [ ] 创建 `backend/app/models/conversion.py` - 转换任务表
  ```python
  - id: 主键
  - file_id: 关联文件ID（外键）
  - source_format: 源格式
  - target_format: 目标格式
  - status: 转换状态（pending/processing/completed/failed）
  - result_path: 转换结果路径
  - error_message: 错误信息
  - created_at: 创建时间
  - completed_at: 完成时间
  ```

- [ ] 创建 `backend/app/models/annotation.py` - 标注数据表
  ```python
  - id: 主键
  - file_id: 关联文件ID（外键）
  - page_number: 页码
  - annotation_type: 标注类型（text/long_text/image/table）
  - field_name: 字段名称（name/date/number/amount等）
  - field_value: 字段值
  - coordinates: 坐标信息（JSON）
  - created_at: 创建时间
  - updated_at: 更新时间
  ```

- [ ] 创建 `backend/app/models/template.py` - 标注模板表
  ```python
  - id: 主键
  - template_name: 模板名称
  - document_type: 文档类型（contract/invoice等）
  - template_data: 模板数据（JSON，包含所有字段定义）
  - created_at: 创建时间
  - updated_at: 更新时间
  ```

- [ ] 编写数据库初始化脚本
- [ ] 测试数据库模型

---

### 第二阶段：文档转换模块 ✅ 已完成

#### 2.1 基础转换功能 ✅ 已完成

**目标：** 实现图片和 Office 文档转 PDF

**后端任务：**
- ✅ 创建 `backend/app/utils/file_utils.py` - 文件工具 ✅
  - `get_file_extension()` - 获取文件扩展名
  - 文件类型检测和验证

- ✅ 创建 `backend/app/services/converter.py` - 格式转换服务 ✅
  - `convert_image_to_pdf()` - 图片转 PDF（使用 Pillow）✅
    - 支持：PNG, JPG, JPEG, GIF, BMP
  - `convert_word_to_pdf()` - Word 转 PDF ✅
    - 使用 LibreOffice（主方案）+ python-docx + reportlab（备用方案）
    - 支持：DOC, DOCX
  - `convert_ofd_to_pdf()` - OFD 转 PDF（使用 PyMuPDF）✅
  - `_convert_word_direct()` - 直接 Word 转换（用于批量）✅
  - `_convert_image_direct()` - 直接图片转换（用于批量）✅
  - `_convert_ofd_with_pymupdf()` - PyMuPDF OFD 转换 ✅

- ✅ 创建 `backend/app/api/convert.py` - 转换 API 路由 ✅
  - `POST /api/convert/to-pdf` - 转换为 PDF ✅
  - `GET /api/convert/status/{conversion_id}` - 查询转换状态 ✅
  - `GET /api/convert/result/{conversion_id}` - 获取转换结果 ✅
  - `GET /api/convert/download/{conversion_id}` - 下载转换结果 ✅
  - `DELETE /api/convert/{conversion_id}` - 删除转换任务 ✅

- ✅ 在 `backend/app/main.py` 中注册转换路由 ✅

**前端任务：**
- ✅ 创建 `frontend/src/api/convert.js` - 转换 API 封装 ✅
  - `convertToPDF()` - 转换为 PDF ✅
  - `getConversionStatus()` - 获取转换状态 ✅
  - `getConversionDownloadUrl()` - 获取下载 URL ✅

- ✅ 创建 `frontend/src/views/Convert.vue` - Word 转 PDF 页面 ✅
  - 文件上传功能 ✅
  - 文件列表展示 ✅
  - 转换功能和进度显示 ✅
  - 下载功能 ✅
  - 删除功能（带确认对话框）✅

- ✅ 创建 `frontend/src/views/ConvertImage.vue` - 图片转 PDF 页面 ✅
  - 完整的转换流程 ✅
  - 上传、转换、下载功能 ✅

- ✅ 创建 `frontend/src/views/ConvertOfd.vue` - OFD 转 PDF 页面 ✅
  - 完整的转换流程 ✅
  - OFD 文件处理 ✅

**测试验证：**
- ✅ 测试 PNG 转 PDF ✅
- ✅ 测试 JPG 转 PDF ✅
- ✅ 测试 GIF 转 PDF ✅
- ✅ 测试 BMP 转 PDF ✅
- ✅ 测试 DOCX 转 PDF ✅
- ✅ 测试 OFD 转 PDF ✅
- ✅ 测试转换进度显示 ✅
- ✅ 测试结果下载 ✅

---

#### 2.2 压缩包处理 ✅ 已完成

**目标：** 支持压缩包上传和批量转换

**后端任务：**
- ✅ 在 `backend/app/services/converter.py` 中实现压缩包处理 ✅
  - `convert_archive_to_pdf()` - 压缩包转 PDF ✅
  - 自动解压 ZIP/RAR 文件 ✅
  - 批量转换支持格式的文件 ✅
  - 将转换后的 PDF 重新打包为 ZIP ✅

- ✅ 更新 `backend/app/api/convert.py` ✅
  - 支持 ZIP、RAR 格式 ✅
  - 返回打包后的 ZIP 文件 ✅

**前端任务：**
- ✅ 创建 `frontend/src/views/ConvertArchive.vue` - 压缩包转 PDF 页面 ✅
  - 上传压缩包功能 ✅
  - 文件列表显示 ✅
  - 批量转换功能 ✅
  - 转换进度显示 ✅
  - 下载 PDF.zip 功能 ✅

**测试验证：**
- ✅ 测试 ZIP 文件解压和转换 ✅
- ✅ 测试 RAR 文件解压和转换 ✅
- ✅ 测试批量转换功能 ✅
- ✅ 测试转换进度显示 ✅
- ✅ 测试 PDF.zip 下载 ✅

**技术实现亮点：**
- ✅ 统一转换逻辑：单独转换和压缩包转换使用相同的底层方法
- ✅ LibreOffice 集成：优先使用 LibreOffice 进行 Word 转换，保证格式准确
- ✅ 多格式支持：支持 Word、图片、OFD 在压缩包中混合转换
- ✅ 自动清理：临时文件自动清理，避免磁盘空间浪费
- ✅ LocalStorage 持久化：转换记录持久化，刷新页面不丢失

---

### 第三阶段：文档标注与信息抽取模块（核心功能）

#### 3.1 标注工具开发

**目标：** 实现可视化标注功能

**前端任务（重点）：**
- [ ] 创建 `frontend/src/components/Annotator/Canvas.vue` - 标注画布
  - 集成 Fabric.js
  - PDF 页面渲染
  - 矩形框选工具
  - 标注框样式（不同类型不同颜色）
  - 标注框拖拽和缩放
  - 标注框删除

- [ ] 创建 `frontend/src/components/Annotator/ToolPanel.vue` - 工具面板
  - 标注类型选择器
    - 短文本标注
    - 长文本标注（多段落）
    - 图片标注
    - 表格标注
  - 字段名称选择器
    - 合同名称
    - 日期
    - 编号
    - 金额
    - 自定义字段
  - 工具操作按钮（选择、移动、删除）

- [ ] 创建 `frontend/src/components/Annotator/AnnotationList.vue` - 标注列表
  - 显示当前页面所有标注
  - 标注项编辑
  - 标注项删除
  - 标注导航（点击定位）

- [ ] 创建 `frontend/src/components/Annotator/FieldEditor.vue` - 字段编辑器
  - 字段名称编辑
  - 字段值编辑
  - 字段类型设置

- [ ] 重构 `frontend/src/views/Annotator.vue` - 标注主页面
  - 左侧：PDF 预览 + 标注画布
  - 右侧：工具面板 + 标注列表
  - 顶部：操作栏（保存、导出、导入模板）
  - 底部：页面导航

- [ ] 创建 `frontend/src/api/annotate.js` - 标注 API 封装
  - `saveAnnotations()` - 保存标注
  - `loadAnnotations()` - 加载标注
  - `exportTemplate()` - 导出模板
  - `importTemplate()` - 导入模板
  - `applyTemplate()` - 应用模板（自动抽取）

**后端任务：**
- [ ] 创建 `backend/app/schemas/annotation.py` - 标注 Schema
  - AnnotationCreate
  - AnnotationUpdate
  - AnnotationResponse
  - TemplateCreate
  - TemplateResponse

- [ ] 创建 `backend/app/services/annotator.py` - 标注服务
  - `save_annotations()` - 保存标注数据
  - `load_annotations()` - 加载标注数据
  - `delete_annotation()` - 删除标注
  - `create_template()` - 创建标注模板
  - `get_templates()` - 获取模板列表

- [ ] 创建 `backend/app/api/annotate.py` - 标注 API 路由
  - `POST /api/annotations` - 保存标注
  - `GET /api/annotations/{file_id}` - 获取文件标注
  - `DELETE /api/annotations/{annotation_id}` - 删除标注
  - `POST /api/templates` - 创建模板
  - `GET /api/templates` - 获取模板列表
  - `POST /api/templates/{template_id}/apply` - 应用模板

- [ ] 在 `backend/app/main.py` 中注册标注路由

**测试验证：**
- [ ] 测试矩形框选功能
- [ ] 测试不同标注类型
- [ ] 测试标注保存和加载
- [ ] 测试标注编辑和删除
- [ ] 测试多页面标注

---

#### 3.2 信息抽取功能

**目标：** 基于标注样本自动抽取信息

**后端任务（核心）：**
- [ ] 创建 `backend/app/utils/pdf_utils.py` - PDF 工具
  - `extract_text_from_pdf()` - 提取 PDF 文本
  - `extract_text_by_coordinates()` - 根据坐标提取文本
  - `extract_images_from_pdf()` - 提取 PDF 图片
  - `extract_tables_from_pdf()` - 提取 PDF 表格

- [ ] 创建 `backend/app/services/extractor.py` - 信息抽取服务
  - **基于规则的抽取：**
    - `extract_by_regex()` - 正则表达式匹配（日期、金额等）
    - `extract_by_keywords()` - 关键词匹配
  - **基于位置的抽取：**
    - `extract_by_coordinates()` - 坐标匹配
    - `find_similar_regions()` - 查找相似区域
  - **基于模板的抽取：**
    - `apply_template_extraction()` - 应用模板自动抽取
    - `calculate_similarity()` - 计算区域相似度
  - **合同专用抽取：**
    - `extract_contract_name()` - 抽取合同名称
    - `extract_contract_date()` - 抽取合同日期
    - `extract_contract_number()` - 抽取合同编号
    - `extract_contract_amount()` - 抽取合同金额

- [ ] 更新 `backend/app/api/annotate.py`
  - 添加自动抽取接口
  - 返回抽取结果和置信度

**前端任务：**
- [ ] 更新 `frontend/src/views/Annotator.vue`
  - 添加"应用模板"功能
  - 显示自动抽取结果
  - 结果确认和修正界面

**测试验证：**
- [ ] 测试合同名称抽取
- [ ] 测试日期抽取
- [ ] 测试编号抽取
- [ ] 测试金额抽取
- [ ] 测试长文本抽取
- [ ] 测试图片区域识别
- [ ] 测试表格识别
- [ ] 测试模板应用功能

---

### 第四阶段：PDF 编辑模块

#### 4.1 文本编辑

**目标：** 实现 PDF 文本内容编辑

**后端任务：**
- [ ] 创建 `backend/app/services/pdf_editor.py` - PDF 编辑服务
  - `edit_text()` - 编辑文本（基于 PyMuPDF）
  - `add_text()` - 添加文本
  - `delete_text()` - 删除文本
  - `update_text_style()` - 修改文本样式

- [ ] 创建 `backend/app/api/edit.py` - 编辑 API 路由
  - `POST /api/edit/text` - 编辑文本
  - `POST /api/edit/save` - 保存编辑结果

**前端任务：**
- [ ] 创建 `frontend/src/components/PDFEditor/TextEditor.vue` - 文本编辑器
- [ ] 创建 `frontend/src/api/edit.js` - 编辑 API 封装
- [ ] 重构 `frontend/src/views/Editor.vue` - 编辑主页面

**测试验证：**
- [ ] 测试文本编辑功能
- [ ] 测试文本添加功能
- [ ] 测试编辑保存功能

---

#### 4.2 注释和批注

**目标：** 添加高亮、下划线、文字注释

**后端任务：**
- [ ] 更新 `backend/app/services/pdf_editor.py`
  - `add_highlight()` - 添加高亮
  - `add_underline()` - 添加下划线
  - `add_comment()` - 添加文字注释

**前端任务：**
- [ ] 创建 `frontend/src/components/PDFEditor/AnnotationTools.vue` - 注释工具
  - 高亮工具
  - 下划线工具
  - 文字批注工具

**测试验证：**
- [ ] 测试高亮功能
- [ ] 测试下划线功能
- [ ] 测试文字批注功能

---

#### 4.3 页面管理

**目标：** 添加、删除、旋转、重排页面

**后端任务：**
- [ ] 更新 `backend/app/services/pdf_editor.py`
  - `add_page()` - 添加页面
  - `delete_page()` - 删除页面
  - `rotate_page()` - 旋转页面
  - `reorder_pages()` - 重排页面
  - `merge_pdfs()` - 合并 PDF

**前端任务：**
- [ ] 创建 `frontend/src/components/PDFEditor/PageManager.vue` - 页面管理器
  - 缩略图展示
  - 拖拽排序
  - 旋转操作
  - 删除操作

**测试验证：**
- [ ] 测试页面添加
- [ ] 测试页面删除
- [ ] 测试页面旋转
- [ ] 测试页面重排

---

#### 4.4 表单编辑

**目标：** 编辑 PDF 表单字段

**后端任务：**
- [ ] 更新 `backend/app/services/pdf_editor.py`
  - `get_form_fields()` - 获取表单字段
  - `update_form_field()` - 更新表单字段值

**前端任务：**
- [ ] 创建表单编辑界面
- [ ] 表单字段列表显示
- [ ] 表单字段值编辑

**测试验证：**
- [ ] 测试表单字段识别
- [ ] 测试表单字段编辑

---

## 📁 目录结构规划

### 后端目录结构

```
backend/
├── app/
│   ├── main.py                 # ✅ 已完成
│   ├── config.py               # ✅ 已完成
│   ├── database.py             # ✅ 已完成
│   ├── models/                 # ❌ 待开发
│   │   ├── __init__.py
│   │   ├── file.py            # 文件模型
│   │   ├── conversion.py      # 转换任务模型
│   │   ├── annotation.py      # 标注模型
│   │   └── template.py        # 模板模型
│   ├── schemas/                # ❌ 待开发
│   │   ├── __init__.py
│   │   ├── file.py            # 文件 Schema
│   │   ├── conversion.py      # 转换 Schema
│   │   ├── annotation.py      # 标注 Schema
│   │   └── edit.py            # 编辑 Schema
│   ├── api/                    # ❌ 待开发
│   │   ├── __init__.py
│   │   ├── upload.py          # 上传 API
│   │   ├── convert.py         # 转换 API
│   │   ├── edit.py            # 编辑 API
│   │   └── annotate.py        # 标注 API
│   ├── services/               # ❌ 待开发
│   │   ├── __init__.py
│   │   ├── file_handler.py    # 文件处理服务
│   │   ├── converter.py       # 转换服务
│   │   ├── archive_handler.py # 压缩包处理服务
│   │   ├── pdf_editor.py      # PDF 编辑服务
│   │   ├── annotator.py       # 标注服务
│   │   └── extractor.py       # 信息抽取服务
│   └── utils/                  # ❌ 待开发
│       ├── __init__.py
│       ├── file_utils.py      # 文件工具
│       ├── pdf_utils.py       # PDF 工具
│       └── image_utils.py     # 图像工具
├── uploads/                    # ✅ 已创建
├── outputs/                    # ✅ 已创建
├── temp/                       # ✅ 已创建
└── requirements.txt            # ✅ 已完成
```

### 前端目录结构

```
frontend/
├── src/
│   ├── main.js                 # ✅ 已完成
│   ├── App.vue                 # ✅ 已完成
│   ├── views/                  # 🔄 部分完成
│   │   ├── Home.vue           # ✅ 已完成
│   │   ├── Upload.vue         # 🔄 UI 完成，需对接 API
│   │   ├── Convert.vue        # ❌ 待开发
│   │   ├── Editor.vue         # ❌ 待开发
│   │   └── Annotator.vue      # ❌ 待开发
│   ├── components/             # ❌ 待开发
│   │   ├── FileList.vue       # 文件列表组件
│   │   ├── PDFPreview.vue     # PDF 预览组件
│   │   ├── PDFEditor/         # PDF 编辑器组件集
│   │   │   ├── Toolbar.vue
│   │   │   ├── TextEditor.vue
│   │   │   ├── AnnotationTools.vue
│   │   │   └── PageManager.vue
│   │   └── Annotator/         # 标注组件集
│   │       ├── Canvas.vue
│   │       ├── ToolPanel.vue
│   │       ├── AnnotationList.vue
│   │       └── FieldEditor.vue
│   ├── api/                    # ❌ 待开发
│   │   ├── upload.js          # 上传 API
│   │   ├── convert.js         # 转换 API
│   │   ├── edit.js            # 编辑 API
│   │   └── annotate.js        # 标注 API
│   ├── store/                  # 🔄 基础完成
│   │   └── index.js           # 需完善状态管理
│   ├── router/                 # ✅ 已完成
│   │   └── index.js
│   └── utils/                  # ✅ 基础完成
│       └── request.js         # Axios 封装
└── package.json                # ✅ 已完成
```

---

## 🔧 技术实现要点

### 文档转换技术选型

1. **图片转 PDF**
   - 库：`img2pdf` 或 `Pillow` + `reportlab`
   - 优点：简单、快速、无损
   - 难点：需要处理图片大小和方向

2. **Word 转 PDF**
   - 库：`python-docx` + `reportlab` 或 `pypandoc`
   - 优点：开源、纯 Python
   - 难点：格式保留问题、复杂排版处理

3. **OFD 转 PDF**
   - 库：需要研究专门的 OFD 处理库（如 `ofdpy`）
   - 难点：OFD 是国产格式，库较少

4. **压缩包处理**
   - ZIP：使用 Python 内置 `zipfile`
   - RAR：使用 `rarfile`（需要系统安装 unrar）

### PDF 编辑技术选型

1. **PyMuPDF (fitz)**
   - 功能强大，支持文本编辑、注释、页面操作
   - 性能好
   - 注意：需要编译环境（Windows 需 Visual Studio）

2. **PyPDF2**
   - 纯 Python，无需编译
   - 功能相对有限
   - 适合页面操作、合并、拆分

### 文档标注技术选型

1. **前端标注工具**
   - 库：`Fabric.js`（Canvas 操作）
   - 功能：矩形框选、拖拽、缩放、样式设置

2. **PDF 渲染**
   - 库：`vue-pdf-embed` 或 `pdf.js`
   - 功能：PDF 页面渲染、页面导航

3. **信息抽取算法**
   - **第一阶段（简单）：**
     - 基于坐标的文本提取
     - 正则表达式匹配（日期、金额）
   - **第二阶段（进阶）：**
     - 基于规则的模板匹配
     - 位置相似度计算
   - **第三阶段（高级，可选）：**
     - 机器学习模型（需要训练数据）
     - OCR 文字识别（PaddleOCR）

---

## 🐛 已知问题和注意事项

### 依赖安装问题

- ⚠️ **PyMuPDF** 在 Windows 上需要 Visual Studio 编译环境
  - 临时方案：使用 `requirements_minimal.txt`（仅 PyPDF2）
  - 完整方案：安装 Visual Studio Build Tools

- ⚠️ **Pillow** 也可能遇到编译问题
  - 解决：使用预编译的 wheel 包

### 文件处理注意事项

1. **文件安全**
   - 文件名需要过滤危险字符
   - 防止路径遍历攻击
   - 限制文件大小（50MB）

2. **临时文件清理**
   - 压缩包解压后的临时文件需要定期清理
   - 转换失败的中间文件需要清理

3. **并发处理**
   - 大文件转换建议使用后台任务队列（如 Celery）
   - 避免阻塞主线程

### 前端性能优化

1. **PDF 渲染**
   - 大文件分页加载
   - 使用虚拟滚动
   - 缩略图懒加载

2. **Canvas 性能**
   - 标注对象过多时优化渲染
   - 使用对象池

---

## 📝 开发规范

### 代码规范

1. **后端（Python）**
   - 遵循 PEP 8 规范
   - 使用类型注解
   - 函数添加 docstring
   - 异常处理要完整

2. **前端（Vue 3）**
   - 使用 Composition API
   - 组件命名使用 PascalCase
   - Props 和 Emits 需要类型定义
   - 使用 ESLint

### Git 提交规范

```
feat: 新功能
fix: 修复 bug
docs: 文档更新
style: 代码格式调整
refactor: 重构
test: 测试相关
chore: 构建/工具相关
```

### API 设计规范

1. **RESTful 风格**
   - GET：查询
   - POST：创建
   - PUT/PATCH：更新
   - DELETE：删除

2. **响应格式**
   ```json
   {
     "code": 200,
     "message": "success",
     "data": {}
   }
   ```

3. **错误处理**
   ```json
   {
     "code": 400,
     "message": "文件类型不支持",
     "error": "Invalid file type"
   }
   ```

---

## 🧪 测试计划

### 单元测试

- [ ] 文件处理函数测试
- [ ] 格式转换函数测试
- [ ] PDF 操作函数测试
- [ ] API 接口测试

### 集成测试

- [ ] 文件上传流程测试
- [ ] 文档转换流程测试
- [ ] 标注保存和应用测试
- [ ] PDF 编辑流程测试

### 端到端测试

- [ ] 用户完整操作流程测试
- [ ] 浏览器兼容性测试
- [ ] 性能测试

---

## 📅 里程碑

### Milestone 1: 基础功能 ✅ 已完成 (2025-12-03)
- ✅ 项目架构搭建
- ✅ 文件上传功能
- ✅ 图片转 PDF
- ✅ 基础转换功能

### Milestone 2: 转换模块 ✅ 已完成 (2025-12-04)
- ✅ Office 文档转 PDF (DOC/DOCX)
- ✅ OFD 转 PDF
- ✅ 压缩包处理 (ZIP/RAR)
- ✅ 批量转换
- ✅ 4个独立转换页面
- ✅ 转换逻辑优化

### Milestone 3: 标注模块（预计 2-3 周）
- [ ] 标注工具开发
- [ ] 标注保存和加载
- [ ] 基于规则的信息抽取
- [ ] 模板功能

### Milestone 4: 编辑模块（预计 1-2 周）
- [ ] 文本编辑
- [ ] 注释批注
- [ ] 页面管理
- [ ] 表单编辑

### Milestone 5: 优化和测试（预计 1 周）
- [ ] 性能优化
- [ ] Bug 修复
- [ ] 完整测试
- [ ] 文档完善

---

## 🎓 参考资料

### 技术文档

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [Vue 3 官方文档](https://cn.vuejs.org/)
- [Element Plus 文档](https://element-plus.org/)
- [PyMuPDF 文档](https://pymupdf.readthedocs.io/)
- [Fabric.js 文档](http://fabricjs.com/docs/)

### 相关库

- `PyMuPDF`: PDF 处理
- `PyPDF2`: PDF 操作
- `python-docx`: Word 文档处理
- `Pillow`: 图像处理
- `img2pdf`: 图片转 PDF
- `rarfile`: RAR 解压
- `Fabric.js`: Canvas 操作
- `vue-pdf-embed`: PDF 预览

---

## 📊 进度追踪

### 总体进度

- **基础架构：** 100% ✅ (2025-12-03 完成)
- **文件上传：** 100% ✅ (2025-12-03 完成)
- **文档转换：** 100% ✅ (2025-12-04 完成)
  - ✅ 图片转 PDF (PNG/JPG/JPEG/GIF/BMP)
  - ✅ Word 文档转 PDF (DOC/DOCX)
  - ✅ OFD 转 PDF
  - ✅ 压缩包批量处理 (ZIP/RAR)
  - ✅ 4个独立转换页面
  - ✅ 转换进度显示和文件下载
- **PDF 编辑：** 0% ⏳ (待开发)
- **文档标注：** 0% ⏳ (待开发)

### 已完成的功能模块

1. ✅ 基础架构搭建 (2025-12-03)
2. ✅ 文件上传系统 (2025-12-03)
3. ✅ 数据库模型 (File, Conversion) (2025-12-03)
4. ✅ 图片转 PDF (2025-12-03)
5. ✅ Word 转 PDF (2025-12-04)
6. ✅ OFD 转 PDF (2025-12-04)
7. ✅ 压缩包批量转 PDF (2025-12-04)
8. ✅ 4个转换页面完整实现 (2025-12-04)
9. ✅ 转换逻辑统一优化 (2025-12-04)

### 下一步行动

1. ✅ ~~实现文件上传后端 API~~ (已完成)
2. ✅ ~~创建数据库模型~~ (已完成)
3. ✅ ~~实现图片转 PDF 功能~~ (已完成)
4. ✅ ~~实现 Word 文档转 PDF~~ (已完成)
5. ✅ ~~实现 OFD 转 PDF~~ (已完成)
6. ✅ ~~实现压缩包批量处理~~ (已完成)
7. 🎯 **建议下一步：开发文档标注模块（项目核心功能）**
   - 标注工具开发
   - 信息抽取功能
8. 开发 PDF 编辑模块

### 本次更新内容 (2025-12-04)

**完成的功能：**
- ✅ OFD 转 PDF 完整实现（PyMuPDF 页面渲染方案）
- ✅ 压缩包转 PDF 完整实现（解压→转换→打包）
- ✅ 4个转换页面添加删除确认对话框
- ✅ Word 转换逻辑统一（单独转换调用压缩包转换流程）
- ✅ 下载文件名和 MIME 类型优化
- ✅ 安装 rarfile 库支持 RAR 解压

**技术优化：**
- ✅ LibreOffice 优先用于 Word 转换（格式保真）
- ✅ 转换逻辑统一，避免重复代码
- ✅ 临时文件自动清理机制
- ✅ LocalStorage 持久化转换记录

**已解决的问题：**
- ✅ OFD 转 PDF 格式支持
- ✅ Word 表格格式显示问题
- ✅ 压缩包下载文件名和格式
- ✅ 多后端进程冲突问题
- ✅ 数据库字段缺失问题

---

**最后更新：** 2025-12-04 16:20
**维护者：** 开发团队
**当前版本：** v0.3.0 (文档转换模块完成)
