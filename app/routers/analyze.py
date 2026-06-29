"""
分析 & 翻译路由
提供视频/文案分析、历史记录、翻译、分享等 API
"""

import asyncio
import json
from typing import Optional

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse

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
    delete_history_batch, delete_all_history,
)
from app.services.video_service import (
    validate_video, validate_image,
    save_upload_file, extract_audio, transcribe_audio,
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
# SSE 辅助函数
# ═══════════════════════════════════════════════════════════════

def _sse(event: str, data: dict) -> str:
    """格式化一条 SSE 消息"""
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


# ═══════════════════════════════════════════════════════════════
# POST /api/analyze — 核心分析接口 (SSE 流式)
# ═══════════════════════════════════════════════════════════════

@router.post("/api/analyze")
async def analyze(
    user: User = Depends(require_user),
    copy_text: Optional[str] = Form(None, description="口播文案文本"),
    video: Optional[UploadFile] = File(None, description="视频文件 mp4/mov"),
    image: Optional[UploadFile] = File(None, description="商品图片 jpg/png/webp"),
    lang: str = Form("zh", description="前端页面语种 zh/th，决定分析报告输出语种"),
):
    """
    提交视频/文案进行分析 (SSE 流式返回进度)

    三种输入方式至少提供一种：
    1. 粘贴口播文案 (copy_text)
    2. 上传视频文件 (video) → 自动提取音频并转写
    3. 可选上传商品图片 (image) → 结合分析

    lang 参数由前端根据页面语言自动传入，
    决定分析报告的语种（zh=中文 / th=泰语），
    与视频本身语种无关。

    SSE 事件：
    - progress: 进度更新 (stage 1-4, percent, message, message_th)
    - complete: 分析完成 (完整结果 JSON)
    - error: 出错 (message)
    """

    # ⚠️ 必须在生成器外部读取 UploadFile，否则 StreamingResponse
    # 返回后文件对象已被 Starlette 关闭，导致 "read of closed file"
    video_content = await video.read() if (video and video.filename) else None
    video_filename = video.filename if (video and video.filename) else None

    image_content = await image.read() if (image and image.filename) else None
    image_filename = image.filename if (image and image.filename) else None

    copy_text = copy_text.strip() if copy_text else None

    async def stream(
        video_content,
        video_filename,
        image_content,
        image_filename,
        copy_text,
        lang,
    ):
        transcript = None
        video_path = None
        image_path = None
        has_video = video_content is not None
        has_copy = copy_text is not None

        try:
            # ── 阶段 1: 提取音频（有视频时）───────────
            if has_video:
                yield _sse("progress", {
                    "stage": 1, "percent": 25,
                    "message": "正在提取音频...",
                    "message_th": "กำลังแยกเสียง..."
                })
                await asyncio.sleep(0)

                ok, err = validate_video(video_filename, len(video_content))
                if not ok:
                    yield _sse("error", {"message": err})
                    return

                video_path = await save_upload_file(video_content, video_filename, subdir="videos")

                # ── 阶段 2: 语音转文字 ──────────────────
                yield _sse("progress", {
                    "stage": 2, "percent": 50,
                    "message": "正在语音转文字...",
                    "message_th": "กำลังแปลงเสียงเป็นข้อความ..."
                })
                await asyncio.sleep(0)

                try:
                    audio_path = await extract_audio(video_path)
                    # 单次 Whisper 转写，language=None 自动识别语种
                    transcript = await transcribe_audio(audio_path)
                except RuntimeError as e:
                    yield _sse("error", {"message": f"视频处理失败: {str(e)}"})
                    return
                except Exception as e:
                    yield _sse("error", {"message": f"语音转写失败: {str(e)}"})
                    return

            # ── 处理文案（如果有）─────────────────────
            if has_copy:
                transcript = copy_text  # 已在外部 strip 过

            # ── 处理商品图片（如果有）─────────────────
            has_image = False
            if image_content is not None:
                ok, err = validate_image(image_filename)
                if not ok:
                    yield _sse("error", {"message": err})
                    return
                image_path = await save_upload_file(image_content, image_filename, subdir="images")
                has_image = True

            # ── 校验至少有一种输入 ─────────────────
            if not transcript and not has_image:
                yield _sse("error", {
                    "message": "请提供口播文案、上传视频文件或上传商品图片，至少提供一种"
                })
                return

            # ── 阶段 3: AI 分析 ─────────────────────
            # 如果没有视频（纯文案），跳过前两个阶段，从 75% 开始
            if has_video:
                yield _sse("progress", {
                    "stage": 3, "percent": 75,
                    "message": "AI 正在分析中...",
                    "message_th": "AI กำลังวิเคราะห์..."
                })
            else:
                yield _sse("progress", {
                    "stage": 3, "percent": 75,
                    "message": "AI 正在分析中...",
                    "message_th": "AI กำลังวิเคราะห์..."
                })
            await asyncio.sleep(0)

            # ── 调用 AI ────────────────────────────
            try:
                if has_image and image_path:
                    # 图片分析：根据语种和是否有口播文案选择提示词
                    from app.services.prompt_service import _load_prompt

                    has_video_script = transcript and len(transcript) > 50
                    is_thai = lang == "th"

                    if has_video_script:
                        # 场景A：有完整口播文案 + 商品图
                        prompt_file = "video_analysis_th.txt" if is_thai else "video_analysis.txt"
                        system_prompt = _load_prompt(prompt_file)
                        if is_thai:
                            user_prompt = (
                                f"นี่คือบทพูดของวิดีโอขายสินค้า กรุณาวิเคราะห์ตาม 6 มิติ:\n\n{transcript}\n\n"
                                f"หมายเหตุ: ผู้ใช้ได้อัปโหลดภาพสินค้าด้วย กรุณาวิเคราะห์ร่วมกับข้อมูลในภาพ (บรรจุภัณฑ์ รูปลักษณ์ จุดขาย ฯลฯ)"
                            )
                        else:
                            user_prompt = (
                                f"以下是带货视频的口播文案，请按6维度进行分析：\n\n{transcript}\n\n"
                                f"注意：用户同时上传了商品截图，请结合商品图片中的信息（包装、外观、卖点标注等）进行更精准的分析。"
                            )
                    else:
                        # 场景B：仅商品图
                        prompt_file = "product_analysis_th.txt" if is_thai else "product_analysis.txt"
                        system_prompt = _load_prompt(prompt_file)
                        if is_thai:
                            user_prompt = "กรุณาวิเคราะห์ภาพสินค้าที่อัปโหลด"
                            if transcript:
                                user_prompt += f" คำอธิบายเพิ่มเติมจากผู้ใช้: {transcript}"
                        else:
                            user_prompt = "请分析上传的商品图片"
                            if transcript:
                                user_prompt += f"，用户补充说明：{transcript}"

                    raw_result = await chat_with_image(
                        system_prompt=system_prompt,
                        user_text=user_prompt,
                        image_path=image_path,
                    )
                else:
                    # 纯文本分析（报告语种由前端 lang 决定）
                    messages = build_video_analysis_prompt(transcript, has_image=False, language=lang)
                    raw_result = await _call_with_retry(messages)

                analysis = _parse_analysis_json(raw_result)

            except HTTPException:
                raise
            except Exception as e:
                error_msg = str(e)
                if "400" in error_msg or "Bad Request" in error_msg:
                    yield _sse("error", {
                        "message": "AI 服务暂时拒绝了请求，可能是文案包含敏感词，请修改后重试"
                    })
                    return
                elif "401" in error_msg or "Unauthorized" in error_msg:
                    yield _sse("error", {
                        "message": "AI 服务认证失败，请联系管理员检查 API Key"
                    })
                    return
                elif "429" in error_msg or "Too Many" in error_msg:
                    yield _sse("error", {
                        "message": "AI 服务请求太频繁，请稍后再试"
                    })
                    return
                elif "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                    yield _sse("error", {
                        "message": "AI 服务响应超时，请稍后重试"
                    })
                    return
                else:
                    yield _sse("error", {"message": f"AI 分析失败: {error_msg[:200]}"})
                    return

            # ── 保存记录 ───────────────────────────
            try:
                record = await create_analysis(
                    user_id=user.id,
                    transcript=transcript,
                    analysis_result=analysis,
                    image_path=image_path,
                )
            except Exception as e:
                yield _sse("error", {"message": f"保存记录失败: {str(e)}"})
                return

            # ── 阶段 4: 完成 ──────────────────────
            yield _sse("complete", {
                "success": True,
                "message": "✅ 分析完成",
                "record_id": record.record_id,
                "analysis": analysis,
                "share_token": record.share_token,
                "transcript": transcript,
            })

        except HTTPException as e:
            yield _sse("error", {"message": e.detail})
        except Exception as e:
            yield _sse("error", {"message": f"分析失败: {str(e)[:300]}"})

    return StreamingResponse(
        stream(
            video_content=video_content,
            video_filename=video_filename,
            image_content=image_content,
            image_filename=image_filename,
            copy_text=copy_text,
            lang=lang,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
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
# DELETE /api/history — 删除历史记录
# ═══════════════════════════════════════════════════════════════

@router.delete("/api/history/all")
async def clear_all_history(user: User = Depends(require_user)):
    """清空当前用户全部历史记录"""
    count = await delete_all_history(user.id)
    return {"success": True, "message": f"已删除 {count} 条记录", "deleted": count}


@router.delete("/api/history")
async def batch_delete_history(
    ids: str,
    user: User = Depends(require_user),
):
    """批量删除历史记录 ?ids=id1,id2,id3"""
    record_ids = [rid.strip() for rid in ids.split(",") if rid.strip()]
    count = await delete_history_batch(user.id, record_ids)
    return {"success": True, "message": f"已删除 {count} 条记录", "deleted": count}


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
        # temperature=0.7: 逐字直译对中↔泰无效，需要足够创造性重组语序
        translated = await chat_completion(messages, temperature=0.7, max_tokens=4096)
        return TranslateResponse(
            success=True,
            message="翻译完成",
            translated_text=translated.strip(),
            direction=req.direction,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"翻译失败: {str(e)}")
