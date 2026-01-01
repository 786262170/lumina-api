# Lumina AI API

Lumina AI 图片处理应用后端API，基于 FastAPI 实现。

## 功能特性

- 用户认证与授权（手机号、微信、游客模式）
- AI问答与推荐
- 图片上传与处理（单图/批量）
- 作品管理
- 订阅与支付
- 场景配置管理

## 技术栈

- Python 3.9+
- FastAPI
- SQLAlchemy (MySQL)
- Redis (Token 黑名单、缓存)
- 阿里云 OSS (可选，支持本地存储 mock 模式)
- JWT 认证
- LiteLLM (统一大模型 SDK，支持 OpenAI、GLM、Azure 等)

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 MySQL 服务

#### macOS (使用 Homebrew)

```bash
# 启动 MySQL 服务
brew services start mysql

# 或者手动启动
mysql.server start

# 检查服务状态
brew services list | grep mysql
```

#### Linux

```bash
# Ubuntu/Debian
sudo systemctl start mysql
# 或
sudo service mysql start

# 检查状态
sudo systemctl status mysql
```

#### 创建数据库和用户

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库
CREATE DATABASE lumina_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

# 创建用户（可选，也可以使用 root）
CREATE USER 'lumina_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON lumina_db.* TO 'lumina_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. 启动 Redis 服务

#### macOS (使用 Homebrew)

```bash
# 启动 Redis 服务
brew services start redis

# 或者手动启动
redis-server

# 检查服务状态
redis-cli ping
# 应该返回: PONG
```

#### Linux

```bash
# Ubuntu/Debian
sudo systemctl start redis
# 或
sudo service redis start

# 检查状态
redis-cli ping
```

#### 配置 Redis 密码（可选）

```bash
# 编辑 Redis 配置文件
# macOS: /opt/homebrew/etc/redis.conf
# Linux: /etc/redis/redis.conf

# 找到并修改 requirepass 行
requirepass your_redis_password

# 重启 Redis 服务
brew services restart redis  # macOS
# 或
sudo systemctl restart redis  # Linux
```

### 4. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

**重要配置项：**

```bash
# 数据库配置
DATABASE_URL=mysql+pymysql://lumina_user:your_password@localhost:3306/lumina_db

# Redis 配置（如果设置了密码）
REDIS_URL=redis://:your_redis_password@localhost:6379/0
REDIS_ENABLED=true

# 或者无密码
REDIS_URL=redis://localhost:6379/0
REDIS_ENABLED=true

# 域名配置（生产环境）
API_DOMAIN=api.lumina.ai
STATIC_DOMAIN=static.lumina.ai
BASE_URL=https://api.lumina.ai
```

> 💡 **域名配置说明：**
> - 开发环境可以不配置域名，使用默认的 `http://localhost:8000`
> - 生产环境需要配置 `API_DOMAIN` 和 `STATIC_DOMAIN`
> - 详细配置步骤请参考 [域名配置指南](docs/域名配置指南.md)
> - 快速配置：运行 `./scripts/setup_domains.sh`

### 5. 初始化数据库

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 6. 运行服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. 访问文档

服务启动后，可以通过以下地址访问 API 文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

> 注意：如果修改了 uvicorn 的 `--port` 参数，请相应调整上述 URL 中的端口号。

## API 文档

API 文档遵循 OpenAPI 3.0 规范，详见 `docs/swagger-v1.json`。

## 项目结构

```
lumina-api/
├── app/
│   ├── main.py              # FastAPI应用入口
│   ├── config.py            # 配置管理
│   ├── database.py          # 数据库连接
│   ├── dependencies.py      # 依赖注入
│   ├── models/              # 数据模型
│   ├── schemas/             # Pydantic模型
│   ├── api/v1/              # API路由
│   ├── services/            # 业务逻辑
│   ├── utils/               # 工具函数
│   └── middleware/          # 中间件
├── migrations/              # 数据库迁移
├── tests/                   # 测试文件
└── docs/                    # 文档
```

## 开发

### 数据库迁移

```bash
# 创建新迁移
alembic revision --autogenerate -m "描述"

# 应用迁移
alembic upgrade head

# 回滚迁移
alembic downgrade -1
```

## 许可证

MIT

