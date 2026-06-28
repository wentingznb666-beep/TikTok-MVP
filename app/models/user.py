"""
用户数据模型 — 纯数据类（非 ORM），直接操作 SQLite
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class User:
    """用户实体"""
    id: int
    username: str
    password_hash: str
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """转为字典（用于 API 返回，不含密码哈希）"""
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at,
        }


@dataclass
class Analysis:
    """分析记录实体"""
    id: int
    user_id: int
    record_id: str
    share_token: str
    transcript: Optional[str] = None
    analysis: Optional[str] = None   # JSON 字符串
    image_path: Optional[str] = None
    has_image: bool = False
    created_at: Optional[str] = None

    def to_dict(self) -> dict:
        """转为字典"""
        import json
        return {
            "id": self.id,
            "user_id": self.user_id,
            "record_id": self.record_id,
            "share_token": self.share_token,
            "transcript": self.transcript,
            "analysis": json.loads(self.analysis) if self.analysis else None,
            "image_path": self.image_path,
            "has_image": bool(self.has_image),
            "created_at": self.created_at,
        }
