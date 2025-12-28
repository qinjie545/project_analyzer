#!/bin/bash

# Docker 构建脚本

set -e

echo "🚀 开始构建 Docker 镜像..."

# 构建后端镜像
echo "📦 构建后端镜像..."
docker build -t github-daily-report-backend:latest ./backend

# 构建前端镜像
echo "📦 构建前端镜像..."
docker build -t github-daily-report-frontend:latest ./frontend

echo "✅ 构建完成！"
echo ""
echo "使用以下命令启动服务："
echo "  docker-compose up -d"
