# 日志系统说明

## 概述

本项目实现了完整的日志系统，包括文件日志、日志轮转和自动清理功能。

## 日志配置

### 配置参数

在 `.env` 文件中可以配置以下日志相关参数：

```env
# 日志配置
LOG_MAX_SIZE_MB=50              # 单个日志文件最大大小（MB），达到后自动轮转
LOG_BACKUP_COUNT=5              # 保留的备份文件数量
LOG_CLEANUP_MAX_SIZE_MB=50      # 日志文件清理阈值（MB），超过此大小的文件将被删除
LOG_CLEANUP_ENABLED=true        # 是否启用自动日志清理
LOG_CLEANUP_INTERVAL_HOURS=24   # 自动清理执行间隔（小时）
```

### 默认配置

- **日志目录**: `logs/`
- **主日志文件**: `logs/lumina_api.log` (包含所有级别的日志)
- **错误日志文件**: `logs/error.log` (仅包含 ERROR 级别及以上的日志)
- **文件大小限制**: 50MB
- **备份文件数量**: 5 个
- **清理阈值**: 50MB
- **自动清理间隔**: 24 小时

## 日志轮转

系统使用 `RotatingFileHandler` 实现日志轮转：

- 当日志文件达到 50MB 时，自动进行轮转
- 轮转后的文件会添加数字后缀：`lumina_api.log.1`, `lumina_api.log.2`, 等
- 最多保留 5 个备份文件
- 超过 5 个备份后，最旧的文件会被自动删除

## 自动清理

系统会在应用启动时启动后台任务，定期清理超大日志文件：

- 清理任务每隔 24 小时执行一次（可配置）
- 删除所有超过 50MB 的日志文件（包括轮转后的备份文件）
- 清理操作会记录在日志中

## 使用方法

### 在代码中使用日志

```python
from app.utils.logger import logger

# 输出不同级别的日志
logger.debug("调试信息")
logger.info("普通信息")
logger.warning("警告信息")
logger.error("错误信息")
logger.critical("严重错误信息")
```

### 手动清理日志

通过 API 接口手动触发日志清理：

```bash
# 获取日志信息
curl -X GET "http://localhost:8000/v1/settings/logs/info" \
  -H "Authorization: Bearer YOUR_TOKEN"

# 手动清理日志
curl -X POST "http://localhost:8000/v1/settings/logs/cleanup" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### 运行测试脚本

```bash
python test_logging.py
```

该脚本会：
1. 输出各种级别的测试日志
2. 显示日志目录信息
3. 显示日志配置
4. 执行日志清理
5. 显示清理后的日志信息

## 日志格式

日志输出格式如下：

```
2026-01-03 00:30:42 - lumina_api - INFO - [test_logging.py:24] - 这是一条测试日志
```

格式说明：
- `2026-01-03 00:30:42`: 时间戳
- `lumina_api`: 日志器名称
- `INFO`: 日志级别
- `[test_logging.py:24]`: 代码文件和行号
- `这是一条测试日志`: 日志消息

## 注意事项

1. **日志目录已添加到 `.gitignore`**：日志文件不会被提交到版本控制系统
2. **生产环境建议**：将 `LOG_CLEANUP_INTERVAL_HOURS` 设置为较小的值（如 6-12 小时）
3. **磁盘空间监控**：虽然系统会自动清理超大日志文件，但仍建议定期监控磁盘空间
4. **敏感信息**：请避免在日志中输出敏感信息（如密码、密钥等）

## 文件结构

```
lumina-api/
├── logs/                          # 日志目录（自动创建）
│   ├── lumina_api.log            # 主日志文件
│   ├── lumina_api.log.1          # 轮转备份1
│   ├── lumina_api.log.2          # 轮转备份2
│   ├── error.log                 # 错误日志文件
│   └── error.log.1               # 错误日志备份
├── app/
│   ├── utils/
│   │   ├── logger.py             # 日志配置模块
│   │   └── log_cleanup.py        # 日志清理任务
│   ├── config.py                 # 全局配置（包含日志配置）
│   └── main.py                   # 应用入口（启动清理任务）
└── test_logging.py               # 日志测试脚本
```

## 故障排查

### 日志文件未创建

检查日志目录权限：
```bash
ls -ld logs/
mkdir -p logs/
chmod 755 logs/
```

### 日志清理未生效

1. 检查配置是否启用：`LOG_CLEANUP_ENABLED=true`
2. 查看应用日志，确认清理任务已启动
3. 手动触发清理：使用 API 接口或运行测试脚本

### 日志文件过大

1. 减小 `LOG_MAX_SIZE_MB` 配置值
2. 减小 `LOG_BACKUP_COUNT` 配置值
3. 手动执行清理：`python test_logging.py`
