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
- 阿里云 OSS
- JWT 认证

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填写配置：

```bash
cp .env.example .env
```

### 3. 初始化数据库

```bash
# 创建数据库迁移
alembic revision --autogenerate -m "Initial migration"

# 执行迁移
alembic upgrade head
```

### 4. 运行服务

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 5. 访问文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

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

