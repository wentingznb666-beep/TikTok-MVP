"""
认证路由
提供注册、登录、获取当前用户信息的 API 端点
"""

from fastapi import APIRouter, Depends, Header, HTTPException
from typing import Optional

from app.models.schemas import RegisterRequest, LoginRequest, AuthResponse, UserInfo
from app.services.auth_service import register_user, login_user, get_current_user

router = APIRouter(prefix="/api/auth", tags=["认证"])


# ── 依赖注入：从请求头提取 Bearer token 获取当前用户 ─────────
async def require_user(authorization: Optional[str] = Header(None)):
    """
    从 Authorization 头提取并验证 JWT token
    失败时抛出 401
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="请先登录")
    token = authorization.split(" ", 1)[1]
    user = await get_current_user(token)
    if not user:
        raise HTTPException(status_code=401, detail="登录已过期，请重新登录")
    return user


@router.post("/register", response_model=AuthResponse)
async def register(req: RegisterRequest):
    """用户注册"""
    ok, msg = await register_user(req.username, req.password)
    return AuthResponse(success=ok, message=msg)


@router.post("/login", response_model=AuthResponse)
async def login(req: LoginRequest):
    """用户登录，返回 JWT token"""
    ok, msg, token, username = await login_user(req.username, req.password)
    if not ok:
        raise HTTPException(status_code=401, detail=msg)
    return AuthResponse(
        success=True,
        message=msg,
        token=token,
        username=username,
    )


@router.get("/me", response_model=UserInfo)
async def get_me(user=Depends(require_user)):
    """获取当前登录用户信息（需要 Bearer token）"""
    return UserInfo(
        id=user.id,
        username=user.username,
        created_at=user.created_at or "",
    )
