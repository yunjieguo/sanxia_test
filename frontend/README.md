# PDF 文档处理系统 - 前端

基于 Vue 3 + Vite + Element Plus 的前端应用。

## 技术栈

- Vue 3 - 渐进式 JavaScript 框架
- Vite - 下一代前端构建工具
- Element Plus - Vue 3 组件库
- Vue Router - 路由管理
- Pinia - 状态管理
- Axios - HTTP 客户端
- Fabric.js - Canvas 操作库（用于标注）

## 快速开始

### 1. 安装依赖

```bash
cd frontend
npm install
```

### 2. 启动开发服务器

```bash
npm run dev
```

访问：http://localhost:5173

### 3. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录。

### 4. 预览生产构建

```bash
npm run preview
```

## 项目结构

```
frontend/
├── public/                 # 静态资源
├── src/
│   ├── main.js            # 应用入口
│   ├── App.vue            # 根组件
│   ├── views/             # 页面组件
│   │   ├── Home.vue       # 首页
│   │   ├── Upload.vue     # 文件上传
│   │   ├── Convert.vue    # 文档转换
│   │   ├── Editor.vue     # PDF编辑
│   │   └── Annotator.vue  # 智能标注
│   ├── components/        # 通用组件
│   ├── api/              # API 接口
│   ├── store/            # 状态管理
│   ├── router/           # 路由配置
│   └── utils/            # 工具函数
├── index.html
├── vite.config.js        # Vite 配置
└── package.json
```

## 功能模块

### 1. 文件上传模块
- 支持拖拽上传
- 多文件上传
- 文件类型验证
- 文件大小限制

### 2. 文档转换模块
- 多格式转 PDF
- 批量转换
- 进度显示

### 3. PDF 编辑模块
- 文本编辑
- 表单编辑
- 注释/批注
- 页面管理

### 4. 智能标注模块
- 可视化标注工具
- 样本训练
- 自动信息抽取
- 标注结果管理

## 开发说明

### API 代理配置

在 `vite.config.js` 中已配置了 API 代理：

```javascript
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

### 添加新页面

1. 在 `src/views/` 创建页面组件
2. 在 `src/router/index.js` 添加路由配置
3. 在导航菜单中添加入口

### 调用后端 API

使用封装好的 request 工具：

```javascript
import request from '@/utils/request'

// GET 请求
const data = await request.get('/endpoint')

// POST 请求
const result = await request.post('/endpoint', { data })
```

## 注意事项

- 确保后端服务已启动（http://localhost:8000）
- 开发时使用 npm run dev，生产环境使用 npm run build
- 图标使用 Element Plus Icons
