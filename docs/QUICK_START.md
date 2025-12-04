# 快速启动指南

本文档提供详细的项目启动步骤。

## 前置要求

在开始之前，请确保你的系统已安装：

- **Python 3.9 或更高版本**
  - 检查版本：`python --version` 或 `python3 --version`
  - 下载地址：https://www.python.org/downloads/

- **Node.js 16 或更高版本**
  - 检查版本：`node --version`
  - 下载地址：https://nodejs.org/

- **Git**（可选，用于版本控制）
  - 检查版本：`git --version`

## 第一步：启动后端服务

### 1.1 进入后端目录

```bash
cd backend
```

### 1.2 安装 Python 依赖

使用 pip 安装所需的 Python 包：

```bash
pip install -r requirements.txt
```

如果使用国内网络，可以使用清华镜像加速：

```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 1.3 配置环境变量（可选）

复制环境变量示例文件：

```bash
# Windows
copy .env.example .env

# Linux/Mac
cp .env.example .env
```

使用文本编辑器打开 `.env` 文件，根据需要修改配置。默认配置通常无需修改即可使用。

### 1.4 启动后端服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

参数说明：
- `--reload`: 开发模式，代码修改后自动重启
- `--host 0.0.0.0`: 允许外部访问
- `--port 8000`: 指定端口号

看到以下输出说明启动成功：

```
🚀 PDF文档处理系统 v1.0.0 正在启动...
✅ 数据库初始化完成
✅ 文件目录检查完成
📝 API 文档地址: http://0.0.0.0:8000/docs
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

### 1.5 验证后端服务

打开浏览器访问以下地址：

- 系统信息：http://localhost:8000/
- API 文档：http://localhost:8000/docs
- 健康检查：http://localhost:8000/health

## 第二步：启动前端应用

**打开新的终端窗口**（保持后端服务运行），执行以下步骤：

### 2.1 进入前端目录

```bash
cd frontend
```

### 2.2 安装 Node.js 依赖

```bash
npm install
```

如果安装速度较慢，可以使用淘宝镜像：

```bash
npm install --registry=https://registry.npmmirror.com
```

或者使用 cnpm：

```bash
npm install -g cnpm --registry=https://registry.npmmirror.com
cnpm install
```

### 2.3 启动开发服务器

```bash
npm run dev
```

看到以下输出说明启动成功：

```
  VITE v5.0.2  ready in 500 ms

  ➜  Local:   http://localhost:5173/
  ➜  Network: http://192.168.1.100:5173/
  ➜  press h to show help
```

### 2.4 访问前端应用

打开浏览器访问：http://localhost:5173

你将看到 PDF 文档处理系统的首页。

## 第三步：验证系统功能

### 3.1 检查首页状态

在首页底部的"系统信息"卡片中，查看：
- **后端状态**应该显示为"运行中"（绿色标签）

如果显示"未连接"（红色标签），请检查：
1. 后端服务是否正常运行
2. 端口 8000 是否被占用
3. 防火墙是否阻止了连接

### 3.2 测试文件上传

1. 点击顶部导航栏的 **"文件上传"**
2. 将文件拖拽到上传区域，或点击上传
3. 支持的文件格式：PDF, PNG, JPG, JPEG, DOC, DOCX, OFD, ZIP, RAR
4. 查看上传结果

## 常见问题排查

### 问题 1：后端启动失败

**错误信息**：`ModuleNotFoundError: No module named 'fastapi'`

**解决方法**：
```bash
cd backend
pip install -r requirements.txt
```

---

**错误信息**：`Address already in use`

**解决方法**：端口 8000 被占用，更换端口：
```bash
uvicorn app.main:app --reload --port 8001
```

同时修改前端的 `vite.config.js` 中的代理地址。

---

### 问题 2：前端启动失败

**错误信息**：`ENOENT: no such file or directory, open 'package.json'`

**解决方法**：确认在 frontend 目录下：
```bash
cd frontend
npm install
```

---

**错误信息**：`Port 5173 is already in use`

**解决方法**：端口 5173 被占用，可以：
1. 关闭占用该端口的程序
2. 或在 `vite.config.js` 中修改端口号

---

### 问题 3：前后端无法通信

**症状**：前端页面显示"后端状态：未连接"

**排查步骤**：

1. 确认后端是否正常运行
   ```bash
   # 在浏览器访问
   http://localhost:8000/health
   ```

2. 检查防火墙设置
   - Windows：允许 Python 通过防火墙
   - Linux/Mac：检查 iptables 规则

3. 检查 vite.config.js 中的代理配置
   ```javascript
   proxy: {
     '/api': {
       target: 'http://localhost:8000',  // 确认端口正确
       changeOrigin: true
     }
   }
   ```

4. 查看浏览器控制台的网络请求
   - 按 F12 打开开发者工具
   - 切换到 Network 标签
   - 刷新页面，查看请求是否成功

---

### 问题 4：文件上传失败

**可能原因**：
1. 文件大小超过 50MB 限制
2. 文件格式不支持
3. 后端存储目录权限不足

**解决方法**：
1. 检查文件大小和格式
2. 查看后端日志输出
3. 确认 `backend/uploads` 目录有写入权限

## 生产环境部署

### 后端生产部署

不使用 `--reload` 参数：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### 前端生产构建

```bash
cd frontend
npm run build
```

构建产物在 `frontend/dist` 目录，可以使用 Nginx 或其他 Web 服务器提供服务。

### 使用 Nginx 部署

示例 Nginx 配置：

```nginx
server {
    listen 80;
    server_name your-domain.com;

    # 前端静态文件
    location / {
        root /path/to/frontend/dist;
        try_files $uri $uri/ /index.html;
    }

    # 代理后端 API
    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # 代理文件访问
    location /uploads {
        proxy_pass http://localhost:8000;
    }

    location /outputs {
        proxy_pass http://localhost:8000;
    }
}
```

## 下一步

现在你已经成功启动了系统，可以：

1. 📄 阅读 [API 文档](http://localhost:8000/docs) 了解后端接口
2. 🛠️ 查看项目源码，开始开发具体功能模块
3. 📝 查看 `PROJECT_README.md` 了解项目整体架构
4. 🎯 根据 `README.rd` 中的需求，实现各个功能模块

如有问题，请查看项目文档或联系项目维护者。
