"""
历史记录服务
提供分析记录的增、查、分享功能
"""

import json
import uuid6
from typing import List, Optional

from app.services.database import get_db
from app.models.user import Analysis
from app.models.schemas import HistoryItem, HistoryDetail


async def create_analysis(
    user_id: int,
    transcript: str,
    analysis_result: dict,
    image_path: Optional[str] = None,
) -> Analysis:
    """
    创建一条分析记录

    参数:
        user_id: 用户 ID
        transcript: 转写文本 / 用户输入文案
        analysis_result: 6 维度分析结果（dict）
        image_path: 可选的商品图片路径

    返回:
        创建的分析记录
    """
    db = await get_db()

    record_id = uuid6.uuid8().hex[:12]    # 12 位短 ID，对外展示
    share_token = uuid6.uuid8().hex       # 32 位分享 token
    analysis_json = json.dumps(analysis_result, ensure_ascii=False)
    has_image = 1 if image_path else 0

    await db.execute(
        """INSERT INTO analyses
           (user_id, record_id, share_token, transcript, analysis, image_path, has_image)
           VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (user_id, record_id, share_token, transcript, analysis_json, image_path, has_image),
    )
    await db.commit()

    # 获取自增 ID
    cursor = await db.execute(
        "SELECT id, created_at FROM analyses WHERE record_id = ?", (record_id,)
    )
    row = await cursor.fetchone()

    return Analysis(
        id=row["id"],
        user_id=user_id,
        record_id=record_id,
        share_token=share_token,
        transcript=transcript,
        analysis=analysis_json,
        image_path=image_path,
        has_image=bool(has_image),
        created_at=row["created_at"],
    )


async def get_user_history(user_id: int, limit: int = 50) -> List[HistoryItem]:
    """
    获取用户的历史分析列表（按时间倒序）

    参数:
        user_id: 用户 ID
        limit: 最多返回条数

    返回:
        历史记录摘要列表
    """
    db = await get_db()
    cursor = await db.execute(
        """SELECT record_id, transcript, has_image, created_at, share_token
           FROM analyses
           WHERE user_id = ?
           ORDER BY created_at DESC
           LIMIT ?""",
        (user_id, limit),
    )
    rows = await cursor.fetchall()

    result = []
    for row in rows:
        preview = (row["transcript"] or "")[:100]
        result.append(HistoryItem(
            record_id=row["record_id"],
            transcript_preview=preview,
            has_image=bool(row["has_image"]),
            created_at=row["created_at"],
            share_token=row["share_token"],
        ))
    return result


async def get_analysis_detail(user_id: int, record_id: str) -> Optional[HistoryDetail]:
    """
    获取单条分析记录的详情（仅限本人）

    参数:
        user_id: 当前用户 ID
        record_id: 记录 ID

    返回:
        详情，不存在或无权限返回 None
    """
    db = await get_db()
    cursor = await db.execute(
        """SELECT record_id, transcript, analysis, has_image, image_path, created_at, share_token
           FROM analyses
           WHERE user_id = ? AND record_id = ?""",
        (user_id, record_id),
    )
    row = await cursor.fetchone()
    if not row:
        return None

    return HistoryDetail(
        record_id=row["record_id"],
        transcript=row["transcript"],
        analysis=json.loads(row["analysis"]) if row["analysis"] else None,
        has_image=bool(row["has_image"]),
        image_path=row["image_path"],
        created_at=row["created_at"],
        share_token=row["share_token"],
    )


async def get_shared_analysis(share_token: str) -> Optional[dict]:
    """
    通过分享 token 获取分析记录（无需登录）

    参数:
        share_token: 分享令牌

    返回:
        分析记录字典，不存在返回 None
    """
    db = await get_db()
    cursor = await db.execute(
        """SELECT record_id, transcript, analysis, has_image, created_at
           FROM analyses
           WHERE share_token = ?""",
        (share_token,),
    )
    row = await cursor.fetchone()
    if not row:
        return None

    return {
        "record_id": row["record_id"],
        "transcript": row["transcript"],
        "analysis": json.loads(row["analysis"]) if row["analysis"] else None,
        "has_image": bool(row["has_image"]),
        "created_at": row["created_at"],
    }
