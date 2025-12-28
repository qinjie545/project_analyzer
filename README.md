# OpenSource Daily Report

自动拉取 GitHub 热门项目并发布到微信公众号的项目，包含后端 API 和前端展示界面。

## 功能特性

- 📊 **自动拉取**: 每周五自动拉取 GitHub 最近一周 star 增长最快的项目
- 📝 **内容整理**: 每周六自动整理项目数据，生成分析文章
- 📱 **自动发布**: 每周日自动发布文章到微信公众号
- 🌐 **Web 界面**: Vue 3 前端界面，可视化展示项目数据
- 🤖 **AI 交互记录**: 记录与 AI 的交互历史

## 项目结构

```
opensource_daily_report/
├── backend/                      # 后端代码
│   ├── fetch_github_trending.py  # GitHub 项目拉取脚本
│   ├── organize_content.py       # 内容整理脚本
│   ├── publish_wechat.py         # 微信公众号发布脚本
│   ├── scheduler.py              # 定时任务调度脚本
│   ├── api_server.py             # Flask API 服务器
│   ├── Dockerfile                # 后端 Docker 镜像配置
│   ├── requirements.txt          # Python 依赖
│   └── config.example            # 配置文件示例
├── frontend/                     # 前端代码
│   ├── src/                      # Vue 源代码
│   │   ├── api/                  # API 接口
│   │   ├── router/               # 路由配置
│   │   ├── views/                # 页面组件
│   │   ├── App.vue               # 根组件
│   │   └── main.js               # 入口文件
│   ├── Dockerfile                # 前端生产环境 Docker 镜像配置
│   ├── Dockerfile.dev            # 前端开发环境 Docker 镜像配置
│   ├── nginx.conf                # Nginx 配置文件
│   ├── package.json              # Node.js 依赖
│   └── vite.config.js            # Vite 配置
├── scripts/                      # 脚本目录
│   ├── docker-build.sh          # Docker 构建脚本
│   └── docker-run.sh             # Docker 运行脚本
├── docker-compose.yml            # Docker Compose 生产环境配置
├── docker-compose.dev.yml        # Docker Compose 开发环境配置
├── .env.example                  # 环境变量示例文件
├── .dockerignore                 # Docker 忽略文件
├── data/                         # 数据存储目录（自动创建）
├── articles/                     # 文章存储目录（自动创建）
├── ai_interaction_log.md         # AI 交互记录文件
└── README.md                     # 项目说明文档
```

## Docker 部署（推荐）

使用 Docker 可以快速部署整个项目，无需手动配置环境。

### 前置要求

- Docker 20.10+
- Docker Compose 2.0+

### 快速启动

1. **克隆项目**
```bash
git clone <repository_url>
cd opensource_daily_report
```

2. **配置环境变量**
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，填入你的配置
# GITHUB_TOKEN=your_github_token
# WECHAT_APP_ID=your_wechat_app_id
# WECHAT_APP_SECRET=your_wechat_app_secret
```

3. **启动服务**
```bash
# 使用 docker-compose 启动（推荐）
docker-compose up -d

# 或者使用提供的脚本
./scripts/docker-run.sh
```

4. **访问应用**
- 前端界面: http://localhost:3000
- 后端 API: http://localhost:5000

### Docker 命令

```bash
# 启动服务（后台运行）
docker-compose up -d

# 查看日志
docker-compose logs -f

# 查看特定服务的日志
docker-compose logs -f backend
docker-compose logs -f frontend

# 停止服务
docker-compose down

# 停止并删除数据卷
docker-compose down -v

# 重新构建镜像
docker-compose build

# 重新构建并启动
docker-compose up -d --build

# 查看运行状态
docker-compose ps
```

### 开发模式

使用开发模式可以支持热重载：

```bash
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### 数据持久化

项目数据存储在以下目录，已通过 volume 挂载：
- `./data` - GitHub 项目数据
- `./articles` - 生成的文章
- `./logs` - 日志文件

这些目录会在首次运行时自动创建。

### 健康检查

后端服务包含健康检查，可以通过以下方式查看：

```bash
# 检查容器健康状态
docker-compose ps

# 直接访问健康检查接口
curl http://localhost:5000/api/health
```

## 快速开始（本地开发）

### 后端设置

1. **进入后端目录**
```bash
cd backend
```

2. **安装 Python 依赖**
```bash
pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

3. **配置环境变量**
```bash
# 复制配置文件示例
cp config.example config.py

# 编辑配置文件，填入你的配置
# 或者设置环境变量
export GITHUB_TOKEN="your_github_token"
export WECHAT_APP_ID="your_wechat_app_id"
export WECHAT_APP_SECRET="your_wechat_app_secret"
```

4. **启动 API 服务器**
```bash
python api_server.py
```

API 服务器将在 http://localhost:5000 运行

### 前端设置

1. **进入前端目录**
```bash
cd frontend
```

2. **安装 Node.js 依赖**
```bash
npm install
```

3. **启动开发服务器**
```bash
npm run dev
```

前端应用将在 http://localhost:3000 运行

## 使用方法

### 手动执行后端任务

1. **拉取 GitHub 项目**（每周五）
```bash
cd backend
python fetch_github_trending.py
```

2. **整理内容**（每周六）
```bash
cd backend
python organize_content.py
```

3. **发布文章**（每周日）
```bash
cd backend
python publish_wechat.py
```

### 自动执行（使用定时任务）

1. **使用 Python scheduler**
```bash
cd backend
python scheduler.py
```

2. **使用系统 cron（推荐）**

编辑 crontab：
```bash
crontab -e
```

添加以下内容：
```
# 每周五 09:00 拉取 GitHub 项目
0 9 * * 5 cd /path/to/opensource_daily_report/backend && python fetch_github_trending.py >> ../logs/fetch.log 2>&1

# 每周六 09:00 整理内容
0 9 * * 6 cd /path/to/opensource_daily_report/backend && python organize_content.py >> ../logs/organize.log 2>&1

# 每周日 09:00 发布文章
0 9 * * 0 cd /path/to/opensource_daily_report/backend && python publish_wechat.py >> ../logs/publish.log 2>&1
```

## API 接口

后端提供以下 REST API 接口：

- `GET /api/repos` - 获取所有项目列表
- `GET /api/repos/<limit>` - 获取指定数量的项目列表
- `GET /api/stats` - 获取统计数据（项目总数、Stars、Forks、语言分布等）
- `GET /api/health` - 健康检查
- `POST /api/analyze` - 触发对单个项目的 AI 分析（请求体示例见下文）

## 配置说明

### AI 模型与 MCP（2025-12-12T19:13:01.673Z）

- 后端新增 MCP+LangChain 分析接口：`POST /api/analyze`
- 支持国内 OpenAI 兼容接口的模型：deepseek、qwen（DashScope 兼容模式）
- 兼容占位支持的代理：copilot agent、cursor agent（需对应服务端/企业接口，默认按 OpenAI 兼容调用路径）
- 环境变量（可选，均有默认）：
  - `MODEL_PROVIDER`：默认 `deepseek`，可设为 `qwen`、`copilot`、`cursor`
  - `MODEL_BASE_URL`：当使用 qwen 时可设为 `https://dashscope.aliyuncs.com/compatible-mode/v1`
  - `MODEL_NAME`：模型名称，示例 `deepseek-chat`、`qwen-plus`、`copilot-agent`、`cursor-agent`
  - `COPILOT_BASE_URL`、`COPILOT_MODEL`：用于 Copilot Agent（占位）
  - `CURSOR_BASE_URL`、`CURSOR_MODEL`：用于 Cursor Agent（占位）

请求体示例：
```json
{
  "repo_full_name": "owner/repo",
  "external_api_key": "你的模型APIKey",
  "model_provider": "deepseek",
  "model_base_url": "https://api.deepseek.com",
  "model_name": "deepseek-chat"
}
```
响应中 `data.analysis.meta.api_key_forwarded` 为 true 表示已转发到外部模型；如需接入公众号 MCP，配置 `WECHAT_APP_ID/WECHAT_APP_SECRET` 即可（当前为占位触发）。

### GitHub Token

获取方式：
1. 访问 https://github.com/settings/tokens
2. 点击 "Generate new token"
3. 选择需要的权限（至少需要 `public_repo` 权限）
4. 复制生成的 token

### 微信公众号配置

1. 登录微信公众平台
2. 进入"开发" -> "基本配置"
3. 获取 AppID 和 AppSecret

## 工作流程

1. **周五**: 自动拉取 GitHub 最近一周 star 增长最快的项目，数据保存到 `data/` 目录
2. **周六**: 自动整理项目数据，生成 Markdown 格式的分析文章，保存到 `articles/` 目录
3. **周日**: 自动将文章发布到微信公众号
4. **随时**: 通过前端界面查看项目数据和统计信息

## 前端功能

- 📊 展示项目统计数据（总数、Stars、Forks）
- 💻 显示编程语言分布
- 🚀 展示热门项目列表
- 🔍 支持项目搜索和筛选
- 📱 响应式设计，支持移动端

## AI 交互记录

所有与 AI 的交互记录都保存在 `ai_interaction_log.md` 文件中，包括：
- 用户输入
- AI 响应
- 交互结果

## 开发说明

### 后端开发

- Python 3.7+
- Flask 2.3+
- 使用虚拟环境推荐

### 前端开发

- Node.js 16+
- Vue 3
- Vite
- Element Plus

## 注意事项

1. GitHub API 有速率限制，建议使用 Personal Access Token
2. 微信公众号发布需要配置相应的权限
3. 定时任务需要确保服务器持续运行
4. 建议定期备份 `data/` 和 `articles/` 目录
5. 前端开发时确保后端 API 服务正在运行
6. Docker 部署时确保端口 3000 和 5000 未被占用
7. 生产环境建议使用反向代理（如 Nginx）处理 HTTPS

## 许可证

MIT License

## 贡献

欢迎提交 Issue 和 Pull Request！
