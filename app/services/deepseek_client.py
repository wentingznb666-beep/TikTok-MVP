"""
智谱 AI 客户端 (GLM)
OpenAI 兼容接口，支持纯文本 + Vision 图片理解
"""

import httpx
import json
import base64
from typing import Optional, List, Dict, Any
from app.config import ZHIPU_API_KEY, ZHIPU_BASE_URL, ZHIPU_MODEL, ZHIPU_VISION_MODEL


# 默认超时（分析任务可能需要较长时间）
DEFAULT_TIMEOUT = httpx.Timeout(120.0, read=180.0)


async def chat_completion(
    messages: List[Dict[str, Any]],
    temperature: float = 0.7,
    max_tokens: int = 4096,
    stream: bool = False,
    model: str = None,
) -> str:
    """
    调用智谱 GLM API 发送消息并获取回复

    参数:
        messages: 标准 OpenAI 格式的消息列表
        temperature: 创造性参数 (0-1)
        max_tokens: 最大输出 token 数
        stream: 是否使用流式输出
        model: 可选模型覆盖（默认使用 ZHIPU_MODEL）

    返回:
        AI 回复的文本内容

    异常:
        httpx.HTTPError: 网络或 API 错误
        ValueError: API 返回异常结构
    """
    # 智谱 API 路径：base_url 已经包含 /api/paas/v4，直接拼接 /chat/completions
    url = f"{ZHIPU_BASE_URL}/chat/completions"
    headers = {
        "Authorization": f"Bearer {ZHIPU_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model or ZHIPU_MODEL,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": stream,
    }

    async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()

    if "choices" not in data or len(data["choices"]) == 0:
        raise ValueError(f"智谱 API 返回异常: {data}")

    return data["choices"][0]["message"]["content"]


async def chat_with_image(
    system_prompt: str,
    user_text: str,
    image_path: str,
    image_detail: str = "auto",
) -> str:
    """
    调用智谱 GLM-4V 进行图片理解（Vision 模式）
    自动适配 glm-4v（标准 data: 前缀）和 glm-4v-flash（原始 base64）格式

    参数:
        system_prompt: 系统提示词
        user_text: 用户文本问题
        image_path: 本地图片路径
        image_detail: 图片精度 (low/high/auto)

    返回:
        AI 回复文本
    """
    # 读取图片并转为 base64
    with open(image_path, "rb") as f:
        image_data = base64.b64encode(f.read()).decode("utf-8")

    # 推断 MIME 类型
    ext = image_path.rsplit(".", 1)[-1].lower()
    mime_map = {"jpg": "image/jpeg", "jpeg": "image/jpeg",
                 "png": "image/png", "webp": "image/webp"}
    mime_type = mime_map.get(ext, "image/jpeg")

    # 格式1: 标准 OpenAI Vision 格式（glm-4v / glm-4v-plus 使用）
    url_with_prefix = f"data:{mime_type};base64,{image_data}"

    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                {
                    "type": "image_url",
                    "image_url": {"url": url_with_prefix},
                },
            ],
        },
    ]

    try:
        return await chat_completion(messages, temperature=0.7, max_tokens=2048, model=ZHIPU_VISION_MODEL)
    except Exception as e:
        error_str = str(e)
        # 如果图片格式错误（如 glm-4v-flash 不支持 data: 前缀），
        # 降级为原始 base64 格式重试
        if "1210" in error_str or "图片输入格式" in error_str:
            messages[1]["content"][1]["image_url"]["url"] = image_data
            return await chat_completion(messages, temperature=0.7, max_tokens=2048, model=ZHIPU_VISION_MODEL)
        raise


async def translate_text(
    text: str,
    direction: str = "zh2th",
) -> str:
    """
    中泰互译

    参数:
        text: 待翻译文本
        direction: "zh2th" 中译泰 / "th2zh" 泰译中

    返回:
        翻译结果
    """
    direction_map = {
        "zh2th": "中文翻译为泰语",
        "th2zh": "泰语翻译为中文",
    }
    task_desc = direction_map.get(direction, "翻译")

    messages = [
        {
            "role": "system",
            "content": f"你是一个专业的中泰翻译助手。请将用户输入的文本{task_desc}。只输出翻译结果，不要额外解释。",
        },
        {"role": "user", "content": text},
    ]

    return await chat_completion(messages, temperature=0.3, max_tokens=2048)
