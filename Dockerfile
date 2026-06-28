# TikTok 电商卖家助手 MVP — Docker 镜像
# 核心功能：文案分析 + 图片理解 + 翻译
# 视频转写需要本地安装 ffmpeg + whisper（镜像体积过大，MVP 阶段暂不含）
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖（ffmpeg 用于视频音频提取，curl 用于健康检查）
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖清单并安装 Python 依赖
COPY requirements-docker.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY app/ ./app/
COPY prompts/ ./prompts/

# 创建数据和上传目录
RUN mkdir -p data/uploads data/uploads/videos data/uploads/audio data/uploads/images

# 非 root 运行
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 8000

# 启动服务
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
