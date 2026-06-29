"""
提示词服务
从 prompts/ 目录加载模板，拼接完整的分析/翻译提示词
"""

import os
from typing import Optional

# 项目根目录下的 prompts/ 文件夹
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "prompts")


def _load_prompt(filename: str) -> str:
    """
    加载提示词模板文件
    如果文件不存在则返回内置的默认模板
    """
    filepath = os.path.join(PROMPTS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    # 兜底：内置模板
    return _get_builtin_prompt(filename)


def _get_builtin_prompt(filename: str) -> str:
    """内置默认提示词（防止文件缺失导致服务崩溃）"""
    if "video_analysis" in filename or "translate" not in filename:
        return """你是一个顶级的 TikTok 电商视频分析师，专精于带货短视频的拆解与优化。

请对以下带货视频的口播文案进行 6 维度深度分析。用中文回答，输出结构化的 JSON 格式。

【分析要求】
1. 视频结构拆解：识别黄金前3秒钩子手法、中段卖点排布逻辑、结尾CTA逼单策略
2. 话术技巧提炼：高转化句式、互动提问设计、情绪起伏节奏
3. 受众与情绪分析：目标人群画像、情绪共鸣点
4. 视听画面配合：判断文案与画面是否协调、提出配合建议
5. 差异化亮点与避雷：至少2条亮点+2条避雷建议
6. 复用优化建议：通用脚本框架 + 3条修改方案 + 品类建议 + 泰语版脚本

【输出格式】严格按以下 JSON 结构输出（不要输出其他内容）：
{
  "structure": {
    "hook": "前3秒钩子内容与手法",
    "middle": "中段卖点排布逻辑",
    "cta": "结尾CTA逼单策略"
  },
  "copywriting": {
    "high_conversion_sentences": ["句式1", "句式2"],
    "interaction_questions": ["提问1", "提问2"],
    "emotion_curve": "情绪曲线描述"
  },
  "audience": {
    "persona": "目标人群画像",
    "emotional_resonance": "情绪共鸣点分析"
  },
  "audio_visual": {
    "match_level": "匹配程度评估",
    "suggestions": "画面配合建议"
  },
  "highlights": {
    "strengths": ["亮点1", "亮点2", "亮点3"],
    "warnings": ["避雷1", "避雷2", "避雷3"]
  },
  "optimization": {
    "script_framework": "通用脚本框架",
    "revisions": ["修改方案1", "修改方案2", "修改方案3"],
    "category_suggestions": "品类扩展建议",
    "thai_script": "🇹🇭 泰语版脚本"
  }
}"""
    elif "translate" in filename:
        return """你是一个专业的中泰翻译助手。请将用户输入的文本进行翻译。
- 如果输入是中文，翻译为泰语
- 如果输入是泰语，翻译为中文
只输出翻译结果，不要额外解释。"""


def build_video_analysis_prompt(
    transcript: str,
    has_image: bool = False,
    language: str = "zh",
) -> list:
    """
    构建视频分析的消息列表

    参数:
        transcript: 视频转写文本/用户粘贴的文案
        has_image: 是否附带商品图片
        language: 语种 "zh"（中文）/ "th"（泰语）

    返回:
        DeepSeek API 格式的消息列表
    """
    if language == "th":
        system_prompt = _load_prompt("video_analysis_th.txt")
        user_content = f"นี่คือบทพูดของวิดีโอขายสินค้า กรุณาวิเคราะห์ตาม 6 มิติ:\n\n{transcript}"
        if has_image:
            user_content += "\n\nหมายเหตุ: ผู้ใช้ได้อัปโหลดภาพสินค้าด้วย กรุณาวิเคราะห์ร่วมกับข้อมูลในภาพ"
    else:
        system_prompt = _load_prompt("video_analysis.txt")
        user_content = f"以下是带货视频的口播文案，请按6维度进行分析：\n\n{transcript}"
        if has_image:
            user_content += "\n\n注意：用户同时上传了商品截图，请结合商品信息进行分析。"

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]


def build_translate_prompt(text: str, direction: str = "zh2th") -> list:
    """
    构建翻译的消息列表

    参数:
        text: 待翻译文本
        direction: zh2th(中→泰) / th2zh(泰→中)

    返回:
        DeepSeek API 格式的消息列表
    """
    direction_map = {
        "zh2th": "中文翻译为泰语",
        "th2zh": "泰语翻译为中文",
    }
    task_desc = direction_map.get(direction, "翻译")

    system_prompt = _load_prompt("translate.txt").replace(
        "{direction}", task_desc
    )

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": text},
    ]
