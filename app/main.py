"""
TikTok 电商卖家助手 — FastAPI 应用入口
组装路由、静态文件、生命周期管理
"""

import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import APP_TITLE, APP_VERSION, UPLOAD_DIR
from app.services.database import get_db, close_db
from app.routers.auth import router as auth_router
from app.routers.analyze import router as analyze_router


# ── 生命周期 ─────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用启动/关闭时的初始化与清理"""
    # 启动：初始化数据库连接 + 确保上传目录存在
    await get_db()
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    print(f"🚀 {APP_TITLE} v{APP_VERSION} 已启动")
    yield
    # 关闭：清理数据库连接
    await close_db()
    print("👋 已关闭")


# ── 创建应用 ─────────────────────────────────────────────────
app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    lifespan=lifespan,
)

# ── 注册路由 ─────────────────────────────────────────────────
app.include_router(auth_router)
app.include_router(analyze_router)


# ── 健康检查 ─────────────────────────────────────────────────
@app.get("/api/health", tags=["系统"])
async def health_check():
    """服务健康检查"""
    return {"status": "ok", "app": APP_TITLE, "version": APP_VERSION}


# ── 静态文件 ─────────────────────────────────────────────────
# 挂载 static 目录，提供前端页面和资源
app.mount("/static", StaticFiles(directory="app/static"), name="static")


# ── 前端入口页 ───────────────────────────────────────────────
@app.get("/")
async def root():
    """首页 — 返回登录/主页"""
    login_path = "app/static/login.html"
    if os.path.exists(login_path):
        return FileResponse(login_path)
    return {"message": f"{APP_TITLE} API 已就绪", "version": APP_VERSION}
