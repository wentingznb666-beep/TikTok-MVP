"""
认证服务
提供注册、登录、JWT 签发/验证、用户查询功能
"""

import bcrypt
from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Optional, Tuple

from app.services.database import get_db
from app.config import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRE_DAYS
from app.models.user import User


async def register_user(username: str, password: str) -> Tuple[bool, str]:
    """
    注册新用户
    返回 (成功, 消息)
    """
    db = await get_db()

    # 检查用户名是否已存在
    cursor = await db.execute(
        "SELECT id FROM users WHERE username = ?", (username,)
    )
    existing = await cursor.fetchone()
    if existing:
        return False, "用户名已被注册，请换一个"

    # 哈希密码（bcrypt 自动加盐）
    password_hash = bcrypt.hashpw(
        password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")

    # 写入数据库
    await db.execute(
        "INSERT INTO users (username, password_hash) VALUES (?, ?)",
        (username, password_hash),
    )
    await db.commit()

    return True, "注册成功，请登录"


async def login_user(username: str, password: str) -> Tuple[bool, str, Optional[str], Optional[str]]:
    """
    登录验证
    返回 (成功, 消息, token, username)
    """
    db = await get_db()

    # 查找用户
    cursor = await db.execute(
        "SELECT id, username, password_hash FROM users WHERE username = ?",
        (username,),
    )
    row = await cursor.fetchone()
    if not row:
        return False, "用户名或密码错误", None, None

    # 验证密码
    if not bcrypt.checkpw(
        password.encode("utf-8"), row["password_hash"].encode("utf-8")
    ):
        return False, "用户名或密码错误", None, None

    # 签发 JWT
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "sub": str(row["id"]),
        "username": row["username"],
        "exp": expire,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

    return True, "登录成功", token, row["username"]


async def get_user_by_id(user_id: int) -> Optional[User]:
    """根据 ID 获取用户"""
    db = await get_db()
    cursor = await db.execute(
        "SELECT id, username, password_hash, created_at FROM users WHERE id = ?",
        (user_id,),
    )
    row = await cursor.fetchone()
    if not row:
        return None
    return User(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        created_at=row["created_at"],
    )


async def get_current_user(token: str) -> Optional[User]:
    """
    解析 JWT token 获取当前用户
    返回 None 表示 token 无效或过期
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id = int(payload.get("sub", 0))
        if user_id == 0:
            return None
        return await get_user_by_id(user_id)
    except (JWTError, ValueError):
        return None
