"""
分析 & 翻译路由
提供视频/文案分析、历史记录、翻译、分享等 API
"""

import json
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse

from app.models.schemas import (
    AnalyzeResponse, HistoryItem, HistoryDetail,
    TranslateRequest, TranslateResponse, ShareResponse,
)
from app.routers.auth import require_user
from app.models.user import User
from app.services.deepseek_client import chat_completion, chat_with_image
from app.services.prompt_service import build_video_analysis_prompt, build_translate_prompt
from app.services.history_service import (
    create_analysis, get_user_history,
    get_analysis_detail, get_shared_analysis,
)
from app.services.video_service import (
    validate_video, validate_image,
    save_upload_file, process_video,
)

router = APIRouter(tags=["分析 & 翻译"])


# ── 辅助函数：解析 AI 返回的 JSON ───────────────────────────
def _parse_analysis_json(raw_text: str) -> dict:
    """
    解析 AI 返回的分析结果，多层容错
    策略：清理 markdown → json.loads → json_repair → 降级返回
    json_repair 能自动修复：未转义引号、尾随逗号、缺失逗号等常见 AI 输出问题
    """
    from json_repair import repair_json

    text = raw_text.strip()

    # 1. 移除 markdown 代码块标记
    if text.startswith("```"):
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()

    # 2. 尝试直接解析
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # 3. 使用 json_repair 自动修复（处理未转义引号、尾随逗号等）
    try:
        repaired = repair_json(text)
        return json.loads(repaired)
    except Exception:
        pass

    # 4. 最终降级：返回原始文本（前端可以展示）
    return {"raw_analysis": raw_text, "parse_error": True}


async def _call_with_retry(messages: list, max_retries: int = 2) -> str:
    """
    调用 AI 分析（带重试机制）
    应对 DeepSeek 偶发的 400/429/5xx 错误
    """
    import asyncio
    from app.services.deepseek_client import chat_completion

    last_error = None
    for attempt in range(max_retries):
        try:
            return await chat_completion(messages, temperature=0.7, max_tokens=4096)
        except Exception as e:
            last_error = e
            error_str = str(e)
            # 400 Bad Request 通常是内容问题，重试无用
            if "400" in error_str:
                raise
            # 429/5xx 可以重试
            if attempt < max_retries - 1:
                wait = (attempt + 1) * 1.5  # 递增等待
                await asyncio.sleep(wait)
    raise last_error


# ═══════════════════════════════════════════════════════════════
# POST /api/analyze — 核心分析接口
# ═══════════════════════════════════════════════════════════════

@router.post("/api/analyze", response_model=AnalyzeResponse)
async def analyze(
    user: User = Depends(require_user),
    copy_text: Optional[str] = Form(None, description="口播文案文本"),
    video: Optional[UploadFile] = File(None, description="视频文件 mp4/mov"),
    image: Optional[UploadFile] = File(None, description="商品图片 jpg/png/webp"),
):
    """
    提交视频/文案进行分析

    三种输入方式至少提供一种：
    1. 粘贴口播文案 (copy_text)
    2. 上传视频文件 (video) → 自动提取音频并转写
    3. 可选上传商品图片 (image) → 结合分析
    """
    transcript = None
    video_path = None
    image_path = None

    # ── 1. 处理视频（如果有）─────────────────────────────
    if video and video.filename:
        # 校验格式和大小
        content = await video.read()
        ok, err = validate_video(video.filename, len(content))
        if not ok:
            raise HTTPException(status_code=400, detail=err)

        try:
            transcript, video_path, audio_path = await process_video(content, video.filename)
        except RuntimeError as e:
            raise HTTPException(status_code=500, detail=f"视频处理失败: {str(e)}")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"语音转写失败: {str(e)}")

    # ── 2. 处理文案（如果有）─────────────────────────────
    if copy_text:
        transcript = copy_text.strip()

    # ── 3. 处理商品图片（如果有）─────────────────────────
    has_image = False
    if image and image.filename:
        ok, err = validate_image(image.filename)
        if not ok:
            raise HTTPException(status_code=400, detail=err)
        image_content = await image.read()
        image_path = await save_upload_file(image_content, image.filename, subdir="images")
        has_image = True

    # ── 4. 校验至少有一种输入（文案/视频/图片）──────────
    if not transcript and not has_image:
        raise HTTPException(
            status_code=400,
            detail="请提供口播文案、上传视频文件或上传商品图片，至少提供一种"
        )

    # ── 5. 调用 AI 分析 ───────────────────────────────────
    try:
        if has_image and image_path:
            # ── 图片分析：根据是否有口播文案选择提示词 ──
            from app.services.prompt_service import _load_prompt

            # 判断用户是"纯商品图分析"还是"视频脚本+商品图辅助"
            has_video_script = transcript and len(transcript) > 50

            if has_video_script:
                # 场景A：有完整口播文案 + 商品图 → 视频分析为主，图片辅助
                system_prompt = _load_prompt("video_analysis.txt")
                user_prompt = (
                    f"以下是带货视频的口播文案，请按6维度进行分析：\n\n{transcript}\n\n"
                    f"注意：用户同时上传了商品截图，请结合商品图片中的信息（包装、外观、卖点标注等）进行更精准的分析。"
                )
            else:
                # 场景B：仅商品图（无文案或文案很短）→ 纯商品图分析
                system_prompt = _load_prompt("product_analysis.txt")
                user_prompt = "请分析上传的商品图片"
                if transcript:
                    user_prompt += f"，用户补充说明：{transcript}"

            raw_result = await chat_with_image(
                system_prompt=system_prompt,
                user_text=user_prompt,
                image_path=image_path,
            )
        else:
            # ── 纯文本分析 ──
            messages = build_video_analysis_prompt(transcript, has_image=False)
            raw_result = await _call_with_retry(messages)

        analysis = _parse_analysis_json(raw_result)

    except HTTPException:
        raise  # 直接透传已有的 HTTPException
    except Exception as e:
        error_msg = str(e)
        if "400" in error_msg or "Bad Request" in error_msg:
            raise HTTPException(
                status_code=500,
                detail="AI 服务暂时拒绝了请求，可能是文案包含敏感词，请修改后重试"
            )
        elif "401" in error_msg or "Unauthorized" in error_msg:
            raise HTTPException(status_code=500, detail="AI 服务认证失败，请联系管理员检查 API Key")
        elif "429" in error_msg or "Too Many" in error_msg:
            raise HTTPException(status_code=500, detail="AI 服务请求太频繁，请稍后再试")
        elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
            raise HTTPException(status_code=500, detail="AI 服务响应超时，请稍后重试")
        else:
            raise HTTPException(status_code=500, detail=f"AI 分析失败: {error_msg[:200]}")

    # ── 6. 保存记录 ──────────────────────────────────────
    try:
        record = await create_analysis(
            user_id=user.id,
            transcript=transcript,
            analysis_result=analysis,
            image_path=image_path,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存记录失败: {str(e)}")

    return AnalyzeResponse(
        success=True,
        message="分析完成",
        record_id=record.record_id,
        analysis=analysis,
        share_token=record.share_token,
        transcript=transcript,
    )


# ═══════════════════════════════════════════════════════════════
# GET /api/history — 历史记录列表
# ═══════════════════════════════════════════════════════════════

@router.get("/api/history")
async def history(user: User = Depends(require_user), limit: int = 50):
    """获取当前用户的分析历史"""
    items = await get_user_history(user.id, limit=limit)
    return {
        "success": True,
        "total": len(items),
        "items": [item.model_dump() for item in items],
    }


# ═══════════════════════════════════════════════════════════════
# GET /api/history/{record_id} — 历史记录详情
# ═══════════════════════════════════════════════════════════════

@router.get("/api/history/{record_id}")
async def history_detail(record_id: str, user: User = Depends(require_user)):
    """获取单条分析详情"""
    detail = await get_analysis_detail(user.id, record_id)
    if not detail:
        raise HTTPException(status_code=404, detail="记录不存在或无权访问")
    return {"success": True, "data": detail.model_dump()}


# ═══════════════════════════════════════════════════════════════
# GET /api/share/{token} — 分享链接（无需登录）
# ═══════════════════════════════════════════════════════════════

@router.get("/api/share/{token}", response_model=ShareResponse)
async def shared_analysis(token: str):
    """通过分享 token 查看分析结果（无需登录）"""
    data = await get_shared_analysis(token)
    if not data:
        raise HTTPException(status_code=404, detail="分享链接无效或已过期")
    return ShareResponse(
        success=True,
        record_id=data["record_id"],
        transcript=data["transcript"],
        analysis=data["analysis"],
        has_image=data["has_image"],
        created_at=data["created_at"],
    )


# ═══════════════════════════════════════════════════════════════
# POST /api/translate — 中泰翻译
# ═══════════════════════════════════════════════════════════════

@router.post("/api/translate", response_model=TranslateResponse)
async def translate(req: TranslateRequest, user: User = Depends(require_user)):
    """中泰双向翻译"""
    try:
        messages = build_translate_prompt(req.text, req.direction)
        translated = await chat_completion(messages, temperature=0.3, max_tokens=2048)
        return TranslateResponse(
            success=True,
            message="翻译完成",
            translated_text=translated.strip(),
            direction=req.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")
