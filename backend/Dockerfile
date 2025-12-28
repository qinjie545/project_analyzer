# 使用 Python 3.11 + Debian bookworm 作为基础镜像，避免 trixie 源不稳定
FROM python:3.11-slim-bookworm

# 可选：国内构建镜像源
ARG USE_CN_MIRROR=false

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# 切换为国内 APT 源（仅当 USE_CN_MIRROR=true）并安装系统依赖
RUN if [ "$USE_CN_MIRROR" = "true" ]; then \
      sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list; \
      if [ -f /etc/apt/sources.list.d/debian.sources ]; then \
        sed -i 's|deb.debian.org|mirrors.tuna.tsinghua.edu.cn|g' /etc/apt/sources.list.d/debian.sources; \
      fi; \
    fi && \
    apt-get -o Acquire::Retries=5 update && \
    apt-get install -y --no-install-recommends \
      gcc \
      git \
      libcairo2-dev \
      pkg-config \
      python3-dev \
      fonts-wqy-microhei \
      fonts-wqy-zenhei \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装 Python 依赖（使用清华大学 PyPI 镜像加速）
RUN pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# 复制应用代码
COPY . .

# 创建数据目录
RUN mkdir -p /app/data /app/articles

# 添加启动脚本
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:5000/api/health')" || exit 1

# 设置入口点和启动命令
ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "api_server.py"]
