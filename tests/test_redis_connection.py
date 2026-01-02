#!/usr/bin/env python3
"""
测试 Redis 连接配置
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.utils.redis_client import get_redis_client, is_redis_available, reset_redis_client
from app.utils.logger import logger


def test_redis_connection():
    """测试 Redis 连接"""
    print("=" * 60)
    print("测试 Redis 连接配置")
    print("=" * 60)
    
    # 显示配置信息
    print(f"\n📋 配置信息：")
    print(f"  REDIS_ENABLED: {settings.redis_enabled}")
    print(f"  REDIS_URL: {settings.redis_url}")
    print(f"  REDIS_PASSWORD: {'***' if settings.redis_password else '(未设置)'}")
    
    if not settings.redis_enabled:
        print("\n⚠️  警告: REDIS_ENABLED 为 false，Redis 功能已禁用")
        return False
    
    # 重置客户端以确保使用最新配置
    reset_redis_client()
    
    print(f"\n1️⃣  测试 Redis 连接...")
    try:
        client = get_redis_client()
        if client is None:
            print("   ❌ 无法创建 Redis 客户端")
            return False
        
        # 测试 PING
        result = client.ping()
        if result:
            print("   ✅ Redis 连接成功")
        else:
            print("   ❌ Redis PING 失败")
            return False
    except Exception as e:
        print(f"   ❌ 连接失败: {e}")
        return False
    
    # 测试基本操作
    print(f"\n2️⃣  测试基本操作...")
    try:
        # 测试 SET
        test_key = "lumina:test:connection"
        test_value = "test_value_123"
        client.set(test_key, test_value, ex=10)  # 10秒过期
        print("   ✅ SET 操作成功")
        
        # 测试 GET
        value = client.get(test_key)
        if value == test_value:
            print("   ✅ GET 操作成功，值匹配")
        else:
            print(f"   ⚠️  GET 操作成功，但值不匹配: {value} != {test_value}")
        
        # 测试 DELETE
        client.delete(test_key)
        print("   ✅ DELETE 操作成功")
        
    except Exception as e:
        print(f"   ❌ 操作失败: {e}")
        return False
    
    # 测试 is_redis_available
    print(f"\n3️⃣  测试 is_redis_available()...")
    if is_redis_available():
        print("   ✅ is_redis_available() 返回 True")
    else:
        print("   ❌ is_redis_available() 返回 False")
        return False
    
    # 显示 Redis 信息
    print(f"\n4️⃣  获取 Redis 信息...")
    try:
        info = client.info("server")
        print(f"   ✅ Redis 版本: {info.get('redis_version', 'unknown')}")
        print(f"   ✅ 运行模式: {info.get('redis_mode', 'unknown')}")
        print(f"   ✅ 运行时间: {info.get('uptime_in_seconds', 0)} 秒")
    except Exception as e:
        print(f"   ⚠️  获取信息失败: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Redis 连接测试完成！所有测试通过")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_redis_connection()
    sys.exit(0 if success else 1)

