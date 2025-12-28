#!/bin/bash
# Docker 容器启动脚本 - 自动配置代理

# 如果设置了代理环境变量，配置 git 使用代理
if [ -n "$HTTP_PROXY" ]; then
    echo "配置 Git 代理: $HTTP_PROXY"
    git config --global http.proxy "$HTTP_PROXY"
fi

if [ -n "$HTTPS_PROXY" ]; then
    echo "配置 Git HTTPS 代理: $HTTPS_PROXY"
    git config --global https.proxy "$HTTPS_PROXY"
fi

# 执行原始命令
exec "$@"
