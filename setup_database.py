#!/usr/bin/env python3
"""创建MySQL数据库（如果不存在）"""

import os
from dotenv import load_dotenv
import pymysql

# 加载环境变量
load_dotenv()

def create_database_if_not_exists():
    """创建数据库（如果不存在）"""
    print("=" * 50)
    print("检查并创建MySQL数据库...")
    print("=" * 50)

    db_url = os.getenv('DATABASE_URL')
    print(f"数据库URL: {db_url}")

    try:
        # 解析DATABASE_URL
        conn_str = db_url.replace('mysql+pymysql://', '')
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

        # 先连接到MySQL服务器（不指定数据库）
        print("\n连接到MySQL服务器...")
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            connect_timeout=10
        )

        print("✓ 连接成功!")

        # 检查数据库是否存在
        with connection.cursor() as cursor:
            cursor.execute(f"SHOW DATABASES LIKE '{database}'")
            result = cursor.fetchone()

            if result:
                print(f"\n✓ 数据库 '{database}' 已存在")
            else:
                print(f"\n数据库 '{database}' 不存在，正在创建...")
                cursor.execute(f"CREATE DATABASE `{database}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
                print(f"✓ 数据库 '{database}' 创建成功")

            # 授予用户所有权限
            print(f"\n授予用户 '{username}' 对数据库 '{database}' 的所有权限...")
            cursor.execute(f"GRANT ALL PRIVILEGES ON `{database}`.* TO '{username}'@'%'")
            cursor.execute("FLUSH PRIVILEGES")
            print("✓ 权限授予成功")

        connection.close()

        # 测试连接到新创建的数据库
        print(f"\n测试连接到数据库 '{database}'...")
        connection = pymysql.connect(
            host=host,
            port=port,
            user=username,
            password=password,
            database=database,
            connect_timeout=10
        )
        print("✓ 数据库连接测试成功!")

        connection.close()
        return True

    except Exception as e:
        print(f"\n✗ 操作失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = create_database_if_not_exists()
    if success:
        print("\n🎉 数据库设置完成！")
    else:
        print("\n⚠️  数据库设置失败！")
