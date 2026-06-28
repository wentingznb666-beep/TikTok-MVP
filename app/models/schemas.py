"""
Pydantic 数据校验模型
定义所有 API 请求/响应的数据结构
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ═══════════════════════════════════════════════════════════════
# 认证相关
# ═══════════════════════════════════════════════════════════════

class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(..., min_length=2, max_length=50, description="用户名")
    password: str = Field(..., min_length=4, max_length=100, description="密码")


class LoginRequest(BaseModel):
    """登录请求"""
    username: str = Field(..., min_length=1, description="用户名")
    password: str = Field(..., min_length=1, description="密码")


class AuthResponse(BaseModel):
    """认证响应"""
    success: bool
    message: str
    token: Optional[str] = None       # JWT token（登录成功时返回）
    username: Optional[str] = None


class UserInfo(BaseModel):
    """用户信息"""
    id: int
    username: str
    created_at: str


# ═══════════════════════════════════════════════════════════════
# 分析相关
# ═══════════════════════════════════════════════════════════════

class AnalyzeRequest(BaseModel):
    """分析请求 — 三种输入至少提供一种"""
    copy_text: Optional[str] = Field(None, description="口播文案文本")
    # 视频/图片通过 multipart/form-data 上传，不在此处定义


class AnalyzeResponse(BaseModel):
    """分析响应"""
    success: bool
    message: str
    record_id: Optional[str] = None
    analysis: Optional[dict] = None       # 6 维度分析结果
    share_token: Optional[str] = None     # 分享用的 token
    transcript: Optional[str] = None      # 实际使用的文本（用户输入或转写结果）


class HistoryItem(BaseModel):
    """历史记录摘要（列表用）"""
    record_id: str
    transcript_preview: str      # 文案前 100 字
    has_image: bool
    created_at: str
    share_token: str


class HistoryDetail(BaseModel):
    """历史记录详情"""
    record_id: str
    transcript: str
    analysis: Optional[dict]
    has_image: bool
    image_path: Optional[str]
    created_at: str
    share_token: str


# ═══════════════════════════════════════════════════════════════
# 翻译相关
# ═══════════════════════════════════════════════════════════════

class TranslateRequest(BaseModel):
    """翻译请求"""
    text: str = Field(..., min_length=1, max_length=5000, description="要翻译的文本")
    direction: str = Field("zh2th", description="翻译方向: zh2th(中→泰) / th2zh(泰→中)")


class TranslateResponse(BaseModel):
    """翻译响应"""
    success: bool
    message: str
    translated_text: Optional[str] = None
    direction: Optional[str] = None


# ═══════════════════════════════════════════════════════════════
# 分享相关
# ═══════════════════════════════════════════════════════════════

class ShareResponse(BaseModel):
    """分享链接响应"""
    success: bool
    record_id: Optional[str] = None
    transcript: Optional[str] = None
    analysis: Optional[dict] = None
    has_image: bool = False
    created_at: Optional[str] = None
