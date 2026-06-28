"""
数据库服务 — SQLite 异步操作
管理 users 和 analyses 两张表，提供连接池和初始化
"""

import aiosqlite
import os
from app.config import DATABASE_PATH

# 数据库连接实例（模块级单例）
_db = None


async def get_db() -> aiosqlite.Connection:
    """
    获取数据库连接
    如果尚未初始化则自动连接，并启用 WAL 模式提升并发性能
    """
    global _db
    if _db is None:
        # 确保 data 目录存在
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        _db = await aiosqlite.connect(DATABASE_PATH)
        _db.row_factory = aiosqlite.Row  # 支持按列名访问
        await _db.execute("PRAGMA journal_mode=WAL")  # 写前日志，提高并发
        await _db.execute("PRAGMA foreign_keys=ON")    # 启用外键约束
        await _init_tables(_db)
    return _db


async def _init_tables(db: aiosqlite.Connection):
    """创建数据库表（如果不存在）"""
    # ── 用户表 ──────────────────────────────────────────────
    await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            username    TEXT    NOT NULL UNIQUE,
            password_hash TEXT  NOT NULL,
            created_at  TEXT    NOT NULL DEFAULT (datetime('now'))
        )
    """)

    # ── 分析记录表 ──────────────────────────────────────────
    await db.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id     INTEGER NOT NULL,
            record_id   TEXT    NOT NULL UNIQUE,   -- 对外展示的唯一 ID
            share_token TEXT    NOT NULL UNIQUE,   -- 分享链接的 token
            transcript  TEXT,                      -- 视频转写文本 / 用户输入文案
            analysis    TEXT,                      -- AI 分析结果 JSON
            image_path  TEXT,                      -- 上传的商品图片路径
            has_image   INTEGER NOT NULL DEFAULT 0, -- 是否附带图片
            created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
        )
    """)

    # 创建索引加速查询
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_analyses_user_id ON analyses(user_id)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_analyses_share_token ON analyses(share_token)"
    )
    await db.execute(
        "CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC)"
    )
    await db.commit()


async def close_db():
    """关闭数据库连接"""
    global _db
    if _db:
        await _db.close()
        _db = None
