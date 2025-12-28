# Docker 部署指南

本文档提供详细的 Docker 部署说明。

## 快速开始

### 1. 准备环境

确保已安装：
- Docker 20.10+
- Docker Compose 2.0+

建议构建参数（BuildKit 纯文本进度与禁用 provenance）：
- 终端临时设置（推荐）：
  - macOS/Linux
    ```bash
    export DOCKER_BUILDKIT=1
    export BUILDKIT_PROGRESS=plain
    ```
  - Windows PowerShell
    ```powershell
    $env:DOCKER_BUILDKIT=1; $env:BUILDKIT_PROGRESS="plain"
    ```
- 使用 buildx 手工构建（可选）：
  ```bash
  docker buildx build --provenance=false --progress=plain -t github_daily_report-backend:dev ./backend
  ```
- 国内网络可开启镜像源：在 .env 中设置 `USE_CN_MIRROR=true`（后端镜像会自动切换为清华 APT 源）

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 3. 启动服务

```bash
docker-compose up -d
```

### 4. 访问应用

- 前端: http://localhost:3000
- 后端 API: http://localhost:5000
- 健康检查: http://localhost:5000/api/health

## 常用命令

### 服务管理

```bash
# 启动服务（后台运行）
docker-compose up -d

# 启动服务（前台运行，查看日志）
docker-compose up

# 停止服务
docker-compose down

# 停止服务并删除数据卷
docker-compose down -v

# 重启服务
docker-compose restart

# 查看服务状态
docker-compose ps
```

### 日志管理

```bash
# 查看所有服务日志
docker-compose logs -f

# 查看特定服务日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 查看最近 100 行日志
docker-compose logs --tail=100
```

### 镜像管理

```bash
# 重新构建镜像
docker-compose build

# 重新构建并启动
docker-compose up -d --build

# 构建特定服务
docker-compose build backend
docker-compose build frontend

# 查看镜像
docker images | grep github-daily-report
```

### 容器管理

```bash
# 进入容器
docker-compose exec backend bash
docker-compose exec frontend sh

# 执行容器内命令
docker-compose exec backend python fetch_github_trending.py

# 查看容器资源使用
docker stats
```

## 开发模式

开发模式支持热重载，代码修改后自动生效：

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

## 数据持久化

项目数据存储在以下目录：
- `./data` - GitHub 项目数据
- `./articles` - 生成的文章
- `./logs` - 日志文件

这些目录通过 volume 挂载，数据会持久化到宿主机。

## 环境变量

主要环境变量：

| 变量名 | 说明 | 必需 |
|--------|------|------|
| GITHUB_TOKEN | GitHub API Token | 可选 |
| WECHAT_APP_ID | 微信公众号 AppID | 可选 |
| WECHAT_APP_SECRET | 微信公众号 AppSecret | 可选 |
| FLASK_ENV | Flask 环境（production/development） | 可选 |

## 网络配置

服务使用 Docker 网络进行通信：
- 网络名称: `opensource_daily_report_network`
- 后端服务名: `backend`
- 前端服务名: `frontend`

前端通过 Nginx 代理 `/api` 请求到后端。

## 端口映射

- 前端: `3000:80` (宿主机:容器)
- 后端: `5000:5000` (宿主机:容器)

如需修改端口，编辑 `docker-compose.yml` 文件。

## 健康检查

后端服务包含健康检查：

```bash
# 检查健康状态
curl http://localhost:5000/api/health

# 查看容器健康状态
docker-compose ps
```

## 故障排查

### 服务无法启动

1. 检查端口是否被占用：
```bash
lsof -i :3000
lsof -i :5000
```

2. 查看日志：
```bash
docker-compose logs
```

3. 检查环境变量：
```bash
docker-compose config
```

### 前端无法访问后端 API

1. 检查后端服务是否运行：
```bash
docker-compose ps backend
```

2. 检查网络连接：
```bash
docker-compose exec frontend ping backend
```

3. 检查 Nginx 配置：
```bash
docker-compose exec frontend cat /etc/nginx/conf.d/default.conf
```

### 数据丢失

数据存储在 volume 中，确保：
1. 不要使用 `docker-compose down -v` 删除数据卷
2. 定期备份 `data/` 和 `articles/` 目录

## 生产环境建议

1. **使用 HTTPS**: 配置反向代理（如 Nginx）处理 HTTPS
2. **资源限制**: 在 `docker-compose.yml` 中添加资源限制
3. **日志管理**: 配置日志轮转和集中管理
4. **监控**: 添加监控和告警
5. **备份**: 定期备份数据目录
6. **安全**: 定期更新镜像和依赖

## 示例：添加资源限制

在 `docker-compose.yml` 中添加：

```yaml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

## 示例：配置 HTTPS

使用 Nginx 反向代理：

```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:3000;
    }
}
```
