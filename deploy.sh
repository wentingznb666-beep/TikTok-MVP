#!/bin/bash
# TikTok 电商卖家助手 — 一键部署脚本
# 用法：./deploy.sh [密钥路径]
# 示例：./deploy.sh ~/tencent_key.pem

set -e

KEY="${1:-~/tencent_key.pem}"
HOST="${SSH_HOST:-43.132.210.213}"
USER="${SSH_USER:-root}"
PROJECT_DIR="/app/TikTok-MVP"

echo "🚀 推送代码到 GitHub..."
git push origin main

echo ""
echo "📦 连接服务器部署..."
ssh -i "$KEY" -o StrictHostKeyChecking=no "$USER@$HOST" << 'ENDSSH'
cd /app/TikTok-MVP
git pull origin main

echo ""
echo "🐳 构建 Docker 镜像..."
docker build -t tiktok-mvp .

echo ""
echo "🔄 重启容器..."
docker stop tiktok-mvp 2>/dev/null || true
docker rm tiktok-mvp 2>/dev/null || true
docker run -d --name tiktok-mvp \
  -p 8000:8000 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/.env:/app/.env \
  --restart always \
  tiktok-mvp

echo ""
echo "✅ 部署完成"
sleep 3
docker ps --filter name=tiktok-mvp
echo ""
curl -s http://localhost:8000/api/health
ENDSSH
