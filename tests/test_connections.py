#!/usr/bin/env python3
"""测试MySQL和Redis连接"""

import os
from dotenv import load_dotenv
import pymysql
import redis

# 加载环境变量
load_dotenv()

def test_mysql_connection():
    """测试MySQL连接"""
    print("=" * 50)
    print("测试MySQL连接...")
    print("=" * 50)

    db_url = os.getenv('DATABASE_URL')
    print(f"数据库URL: {db_url}")

    # 解析DATABASE_URL
    # 格式: mysql+pymysql://username:password@host:port/database
    try:
        # 移除 mysql+pymysql:// 前缀
        conn_str = db_url.replace('mysql+pymysql://', '')

        # 分离用户名密码和主机数据库
        auth_part, host_part = conn_str.split('@')
        username, password = auth_part.split(':')
        host_db = host_part.split('/')
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1])
        database = host_db[1]

        print(f"主机: {host}")
        print(f"端口: {port}")
        print(f"数据库: {database}")
        print(f"用户: {username}")

        # 测试连接
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            connect_timeout=10
        )

        print("\n✓ MySQL连接成功!")

        # 执行测试查询
        with connection.cursor() as cursor:
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            print(f"✓ MySQL版本: {version[0]}")

            cursor.execute("SELECT DATABASE()")
            current_db = cursor.fetchone()
            print(f"✓ 当前数据库: {current_db[0]}")

        connection.close()
        return True

    except Exception as e:
        print(f"\n✗ MySQL连接失败: {str(e)}")
        return False

def test_redis_connection():
    """测试Redis连接"""
    print("\n" + "=" * 50)
    print("测试Redis连接...")
    print("=" * 50)

    redis_url = os.getenv('REDIS_URL')
    print(f"Redis URL: {redis_url}")

    try:
        # 解析REDIS_URL
        # 格式: redis://:password@host:port/db
        conn_str = redis_url.replace('redis://', '')

        # 移除密码部分
        if '@' in conn_str:
            pass_part, host_part = conn_str.split('@')
            # 移除开头的 :
            password = pass_part[1:] if pass_part.startswith(':') else pass_part
        else:
            password = None
            host_part = conn_str

        # 解析主机、端口和数据库
        host_db = host_part.split('/')
        host_port = host_db[0].split(':')
        host = host_port[0]
        port = int(host_port[1])
        db = int(host_db[1]) if len(host_db) > 1 else 0

        print(f"主机: {host}")
        print(f"端口: {port}")
        print(f"数据库: {db}")

        # 测试连接
        r = redis.Redis(
            host=host,
            port=port,
            password=password,
            db=db,
            decode_responses=True,
            socket_connect_timeout=10
        )

        # 执行PING命令
        result = r.ping()
        if result:
            print("\n✓ Redis连接成功!")

            # 获取Redis信息
            info = r.info('server')
            print(f"✓ Redis版本: {info.get('redis_version', 'unknown')}")

            # 测试读写
            test_key = "test_connection_key"
            r.set(test_key, "test_value", ex=10)
            value = r.get(test_key)
            print(f"✓ Redis读写测试成功: {value}")

            # 清理测试键
            r.delete(test_key)

            return True
        else:
            print("\n✗ Redis PING失败")
            return False

    except Exception as e:
        print(f"\n✗ Redis连接失败: {str(e)}")
        return False

if __name__ == "__main__":
    print("\n开始测试数据库连接...\n")

    mysql_ok = test_mysql_connection()
    redis_ok = test_redis_connection()

    print("\n" + "=" * 50)
    print("测试结果汇总:")
    print("=" * 50)
    print(f"MySQL连接: {'✓ 成功' if mysql_ok else '✗ 失败'}")
    print(f"Redis连接: {'✓ 成功' if redis_ok else '✗ 失败'}")
    print("=" * 50)

    if mysql_ok and redis_ok:
        print("\n🎉 所有连接测试通过！")
    else:
        print("\n⚠️  部分连接测试失败，请检查配置！")
