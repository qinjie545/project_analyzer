#!/bin/bash
# 重启 Docker 容器并配置代理

# 将系统代理中的 127.0.0.1 替换为 host.docker.internal（供容器访问宿主机）
export HTTP_PROXY="${HTTP_PROXY//127.0.0.1/host.docker.internal}"
export HTTPS_PROXY="${HTTPS_PROXY//127.0.0.1/host.docker.internal}"
export http_proxy="${http_proxy//127.0.0.1/host.docker.internal}"
export https_proxy="${https_proxy//127.0.0.1/host.docker.internal}"

echo "使用代理配置："
echo "  HTTP_PROXY: $HTTP_PROXY"
echo "  HTTPS_PROXY: $HTTPS_PROXY"

# 重启容器
docker-compose down
docker-compose up -d

echo ""
echo "容器已重启，检查代理设置..."
sleep 5
docker exec opensource_daily_report_backend bash -c 'echo "容器内代理: HTTP_PROXY=$HTTP_PROXY"'
