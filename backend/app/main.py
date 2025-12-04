"""FastAPI 应用主入口"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .config import settings
from .database import init_db
import os

# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="一个集成了文档转换、PDF编辑和智能标注的文档处理系统",
    debug=settings.DEBUG
)

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 挂载静态文件目录
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
app.mount("/outputs", StaticFiles(directory=settings.OUTPUT_DIR), name="outputs")


@app.on_event("startup")
async def startup_event():
    """应用启动时执行"""
    print(f"[启动] {settings.APP_NAME} v{settings.APP_VERSION} 正在启动...")

    # 初始化数据库
    init_db()
    print("[完成] 数据库初始化完成")

    # 确保必要的目录存在
    for directory in [settings.UPLOAD_DIR, settings.OUTPUT_DIR, settings.TEMP_DIR]:
        os.makedirs(directory, exist_ok=True)
    print("[完成] 文件目录检查完成")

    print(f"[文档] API 文档地址: http://{settings.HOST}:{settings.PORT}/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时执行"""
    print(f"[关闭] {settings.APP_NAME} 正在关闭...")


@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy"}


# 导入路由
from .api import upload, convert
app.include_router(upload.router)
app.include_router(convert.router)

# 待实现的路由（稍后创建）
# from .api import edit, annotate
# app.include_router(edit.router, prefix="/api/edit", tags=["PDF编辑"])
# app.include_router(annotate.router, prefix="/api/annotate", tags=["智能标注"])
