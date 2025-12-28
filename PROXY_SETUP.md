# GitHub 代理配置说明

## 问题
Docker 容器内无法直接访问 GitHub，报错：
```
fatal: unable to access 'https://github.com/...': Failed to connect to github.com port 443
```

## 解决方案
已配置容器使用宿主机代理（通过 Docker 网桥 172.17.0.1:7890）

### 配置内容

1. **docker-compose.yml** - 添加了代理环境变量
   ```yaml
   environment:
     - HTTP_PROXY=http://172.17.0.1:7890
     - HTTPS_PROXY=http://172.17.0.1:7890
     - http_proxy=http://172.17.0.1:7890
     - https_proxy=http://172.17.0.1:7890
     - NO_PROXY=localhost,127.0.0.1,mysql,*.local
   extra_hosts:
     - "host.docker.internal:host-gateway"
   ```

2. **backend/docker-entrypoint.sh** - 容器启动时自动配置 Git 代理
   - 读取环境变量 HTTP_PROXY 和 HTTPS_PROXY
   - 自动执行 `git config --global http.proxy` 和 `git config --global https.proxy`

3. **backend/Dockerfile** - 使用 ENTRYPOINT 启动脚本

## 使用方法

### 启动容器
```bash
cd /srv/ai/ai-tech-article
docker-compose up -d
```

### 验证配置
```bash
# 检查代理环境变量
docker exec opensource_daily_report_backend env | grep -i proxy

# 检查 git 配置
docker exec opensource_daily_report_backend git config --global --list | grep proxy

# 测试 GitHub 连接
docker exec opensource_daily_report_backend git clone --depth 1 https://github.com/vuejs/vue /tmp/test
```

## 注意事项

1. **代理服务器必须监听 0.0.0.0**（所有地址），不能只监听 127.0.0.1
   - 检查方法：`ss -tlnp | grep :7890` 应显示 `*:7890` 而非 `127.0.0.1:7890`
   
2. **Docker 网桥地址固定为 172.17.0.1**
   - 如果 Docker 网络配置不同，需要修改 docker-compose.yml 中的代理地址

3. **重启容器后配置自动生效**
   - 无需手动配置，entrypoint 脚本会自动设置

4. **如果代理端口改变**
   - 修改 docker-compose.yml 中的代理端口（当前为 7890）
   - 重启容器：`docker-compose restart backend`

## 故障排查

### 问题：仍然无法连接 GitHub
```bash
# 1. 检查代理是否在运行
ss -tlnp | grep :7890

# 2. 从容器内测试代理连接
docker exec opensource_daily_report_backend curl -x http://172.17.0.1:7890 https://www.google.com -I

# 3. 检查防火墙是否阻止 Docker 网桥访问代理
sudo iptables -L -n | grep 172.17
```

### 问题：某些仓库 clone 超时
- 可能是仓库太大，增加超时时间：
  ```bash
  docker exec opensource_daily_report_backend git config --global http.postBuffer 524288000
  docker exec opensource_daily_report_backend git config --global http.lowSpeedLimit 0
  docker exec opensource_daily_report_backend git config --global http.lowSpeedTime 999999
  ```

## 相关文件
- `/srv/ai/ai-tech-article/docker-compose.yml` - Docker Compose 配置
- `/srv/ai/ai-tech-article/backend/Dockerfile` - Backend 镜像构建文件
- `/srv/ai/ai-tech-article/backend/docker-entrypoint.sh` - 容器启动脚本
- `/srv/ai/ai-tech-article/docker-restart.sh` - 快速重启脚本（可选）
