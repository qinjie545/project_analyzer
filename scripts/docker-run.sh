#!/bin/bash

# Docker 运行脚本

set -e

# 检查 .env 文件
if [ ! -f .env ]; then
    echo "⚠️  未找到 .env 文件，正在从 .env.example 创建..."
    cp .env.example .env
    echo "📝 请编辑 .env 文件，填入你的配置信息"
    exit 1
fi

# 创建必要的目录
mkdir -p data articles logs

# 启动服务
echo "🚀 启动 Docker 服务..."
docker-compose up -d

echo "✅ 服务已启动！"
echo ""
echo "📊 后端 API: http://localhost:5001"
echo "🌐 前端界面: http://localhost:3001"
echo ""
echo "查看日志: docker-compose logs -f"
echo "停止服务: docker-compose down"
