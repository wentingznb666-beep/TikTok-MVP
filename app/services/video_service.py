"""
视频处理服务
提供视频提取音频、Whisper 语音转文字功能
"""

import os
import uuid6
import tempfile
import subprocess
from pathlib import Path

from app.config import UPLOAD_DIR, WHISPER_MODEL, WHISPER_LANGUAGE, ALLOWED_VIDEO_EXTENSIONS

# Whisper 模型延迟加载（首次使用时加载，节省启动时间）
_whisper_model = None


def _get_whisper_model():
    """获取 Whisper 模型实例（单例延迟加载）"""
    global _whisper_model
    if _whisper_model is None:
        import whisper
        print(f"📢 正在加载 Whisper {WHISPER_MODEL} 模型...")
        _whisper_model = whisper.load_model(WHISPER_MODEL)
        print(f"✅ Whisper {WHISPER_MODEL} 模型已就绪")
    return _whisper_model


def validate_video(filename: str, file_size: int) -> tuple[bool, str]:
    """
    校验上传的视频文件

    参数:
        filename: 原始文件名
        file_size: 文件大小（字节）

    返回:
        (是否合法, 错误消息)
    """
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_VIDEO_EXTENSIONS:
        return False, f"不支持的视频格式 {ext}，仅支持 mp4/mov"

    max_bytes = 100 * 1024 * 1024  # 100MB
    if file_size > max_bytes:
        return False, f"视频文件不能超过 100MB"

    return True, ""


def validate_image(filename: str) -> tuple[bool, str]:
    """
    校验上传的图片文件

    参数:
        filename: 原始文件名

    返回:
        (是否合法, 错误消息)
    """
    ext = Path(filename).suffix.lower()
    allowed = {".jpg", ".jpeg", ".png", ".webp"}
    if ext not in allowed:
        return False, f"不支持的图片格式 {ext}，仅支持 jpg/png/webp"
    return True, ""


async def save_upload_file(file_content: bytes, original_filename: str, subdir: str = "") -> str:
    """
    保存上传文件到本地

    参数:
        file_content: 文件二进制内容
        original_filename: 原始文件名
        subdir: 子目录（如 'videos' / 'images'）

    返回:
        保存后的文件路径
    """
    ext = Path(original_filename).suffix.lower()
    save_dir = os.path.join(UPLOAD_DIR, subdir)
    os.makedirs(save_dir, exist_ok=True)

    filename = f"{uuid6.uuid8().hex}{ext}"
    filepath = os.path.join(save_dir, filename)

    with open(filepath, "wb") as f:
        f.write(file_content)

    return filepath


async def extract_audio(video_path: str) -> str:
    """
    从视频中提取音频为 WAV 格式（Whisper 需要）

    参数:
        video_path: 视频文件路径

    返回:
        提取出的音频文件路径
    """
    audio_filename = f"{uuid6.uuid8().hex}.wav"
    audio_path = os.path.join(UPLOAD_DIR, "audio", audio_filename)
    os.makedirs(os.path.dirname(audio_path), exist_ok=True)

    # 使用 ffmpeg 提取音频：16kHz 单声道 WAV
    cmd = [
        "ffmpeg", "-i", video_path,
        "-vn",                # 不要视频流
        "-acodec", "pcm_s16le",  # 16-bit PCM
        "-ar", "16000",       # 16kHz 采样率
        "-ac", "1",           # 单声道
        "-y",                 # 覆盖已有文件
        audio_path,
    ]

    try:
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
    except subprocess.CalledProcessError as e:
        raise RuntimeError(f"音频提取失败: {e.stderr}")

    return audio_path


async def transcribe_audio(audio_path: str, language: str = None) -> str:
    """
    使用 Whisper 将音频转为文字

    参数:
        audio_path: 音频文件路径
        language: 语言代码（默认使用配置的 WHISPER_LANGUAGE）

    返回:
        转写文本
    """
    if language is None:
        language = WHISPER_LANGUAGE

    model = _get_whisper_model()

    # 在异步环境中运行同步的 Whisper 转写
    import asyncio
    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
        None,
        lambda: model.transcribe(audio_path, language=language)
    )

    return result["text"].strip()


async def process_video(video_content: bytes, filename: str) -> tuple[str, str, str]:
    """
    完整视频处理管线：保存 → 提取音频 → 转文字

    参数:
        video_content: 视频二进制数据
        filename: 原始文件名

    返回:
        (转写文本, 视频文件路径, 音频文件路径)
    """
    # 1. 保存视频
    video_path = await save_upload_file(video_content, filename, subdir="videos")

    # 2. 提取音频
    audio_path = await extract_audio(video_path)

    # 3. 语音转文字
    transcript = await transcribe_audio(audio_path)

    return transcript, video_path, audio_path
