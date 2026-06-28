"""
应用配置中心
从 .env 读取环境变量，提供统一的配置入口
"""

import os
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()

# ── 智谱 AI API (GLM) ───────────────────────────────────────
ZHIPU_API_KEY = os.getenv("ZHIPU_API_KEY", "")
ZHIPU_BASE_URL = os.getenv("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
ZHIPU_MODEL = os.getenv("ZHIPU_MODEL", "glm-4-flash")        # 文本模型，max_tokens=4096
ZHIPU_VISION_MODEL = os.getenv("ZHIPU_VISION_MODEL", "glm-4v")  # 视觉模型，max_tokens=2048

# ── JWT 认证 ────────────────────────────────────────────────
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7  # Token 有效期 7 天

# ── 数据库 ──────────────────────────────────────────────────
DATABASE_PATH = os.getenv("DATABASE_PATH", "data/app.db")

# ── 文件存储 ────────────────────────────────────────────────
UPLOAD_DIR = os.getenv("UPLOAD_DIR", "data/uploads")
MAX_VIDEO_SIZE_MB = 100  # 视频最大 100MB
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov"}

# ── Whisper 模型 ────────────────────────────────────────────
WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")  # base 模型，平衡速度与准确率
WHISPER_LANGUAGE = os.getenv("WHISPER_LANGUAGE", "zh")  # 默认中文识别

# ── 应用信息 ────────────────────────────────────────────────
APP_TITLE = "TikTok 电商卖家助手"
APP_VERSION = "0.1.0"
