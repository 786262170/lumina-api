#!/usr/bin/env python3
"""
测试日志功能的脚本
"""
import sys
import time
from pathlib import Path

# 确保可以导入 app 模块
sys.path.insert(0, str(Path(__file__).parent))

from app.utils.logger import logger, cleanup_old_logs, get_log_size_info
from app.config import settings


def test_logging():
    """测试日志功能"""
    print("=" * 60)
    print("测试日志功能")
    print("=" * 60)

    # 1. 测试基本日志输出
    print("\n1. 测试基本日志输出...")
    logger.info("这是一条测试日志")
    logger.debug("这是一条调试日志")
    logger.warning("这是一条警告日志")
    logger.error("这是一条错误日志")
    print("✓ 日志输出成功")

    # 2. 显示日志目录信息
    print("\n2. 日志目录信息:")
    log_info = get_log_size_info()
    print(f"   - 日志文件数量: {log_info['file_count']}")
    print(f"   - 总大小: {log_info['total_size_mb']} MB")

    # 3. 显示配置信息
    print("\n3. 日志配置:")
    print(f"   - 最大文件大小: {settings.log_max_size_mb} MB")
    print(f"   - 备份文件数量: {settings.log_backup_count}")
    print(f"   - 清理阈值: {settings.log_cleanup_max_size_mb} MB")
    print(f"   - 自动清理: {'启用' if settings.log_cleanup_enabled else '禁用'}")
    print(f"   - 清理间隔: {settings.log_cleanup_interval_hours} 小时")

    # 4. 测试日志清理功能
    print("\n4. 测试日志清理功能...")
    print("   执行日志清理...")
    cleanup_old_logs(max_size_mb=settings.log_cleanup_max_size_mb)
    print("✓ 日志清理完成")

    # 5. 再次显示日志目录信息
    print("\n5. 清理后的日志目录信息:")
    log_info = get_log_size_info()
    print(f"   - 日志文件数量: {log_info['file_count']}")
    print(f"   - 总大小: {log_info['total_size_mb']} MB")

    print("\n" + "=" * 60)
    print("测试完成！")
    print("=" * 60)
    print("\n日志文件位置:")
    logs_dir = Path("logs")
    if logs_dir.exists():
        for log_file in sorted(logs_dir.glob("*.log*")):
            size_mb = log_file.stat().st_size / 1024 / 1024
            print(f"  - {log_file.name} ({size_mb:.2f} MB)")
    else:
        print("  (日志目录不存在)")


if __name__ == "__main__":
    test_logging()
