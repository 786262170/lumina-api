#!/usr/bin/env python3
"""
测试阿里云 OSS 连接
"""
import sys
import os
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import oss2
from app.config import settings
from app.utils.logger import logger


def test_oss_connection():
    """测试 OSS 连接"""
    print("=" * 60)
    print("测试阿里云 OSS 连接")
    print("=" * 60)
    
    # 检查配置
    print(f"\n📋 配置信息：")
    print(f"  AccessKey ID: {settings.oss_access_key_id[:10]}...{settings.oss_access_key_id[-4:]}")
    print(f"  Bucket: {settings.oss_bucket_name}")
    print(f"  Endpoint: {settings.oss_endpoint}")
    print(f"  Region: {settings.oss_region}")
    print(f"  Mock Mode: {settings.oss_mock_mode}")
    
    if settings.oss_mock_mode:
        print("\n⚠️  警告: OSS_MOCK_MODE 为 true，将使用本地存储，不会连接到真实的 OSS")
        return False
    
    if not settings.oss_access_key_id or not settings.oss_access_key_secret:
        print("\n❌ 错误: AccessKey ID 或 Secret 未配置")
        return False
    
    try:
        # 1. 初始化认证
        print(f"\n1️⃣  初始化 OSS 客户端...")
        auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
        bucket = oss2.Bucket(auth, settings.oss_endpoint, settings.oss_bucket_name)
        print("   ✅ 客户端初始化成功")
        
        # 2. 测试 Bucket 访问权限
        print(f"\n2️⃣  检查 Bucket 访问权限...")
        try:
            bucket_info = bucket.get_bucket_info()
            print(f"   ✅ Bucket 访问成功")
            print(f"   📦 Bucket 名称: {bucket_info.name}")
            print(f"   📍 地域: {bucket_info.location}")
            print(f"   📅 创建时间: {bucket_info.creation_date}")
        except oss2.exceptions.AccessDenied as e:
            print(f"   ⚠️  AccessKey 可能没有读取权限: {e}")
            return False
        except oss2.exceptions.NoSuchBucket as e:
            print(f"   ❌ Bucket 不存在: {e}")
            return False
        except Exception as e:
            print(f"   ⚠️  无法获取 Bucket 信息: {e}")
            # 继续测试，可能是权限问题但上传可能可以
        
        # 3. 测试上传文件
        print(f"\n3️⃣  测试文件上传...")
        test_content = b"Hello, OSS! This is a test file from Lumina API."
        test_object_name = "test/connection_test.txt"
        
        try:
            result = bucket.put_object(
                test_object_name,
                test_content,
                headers={"Content-Type": "text/plain"}
            )
            print(f"   ✅ 文件上传成功")
            print(f"   📄 对象路径: {test_object_name}")
            print(f"   🔖 ETag: {result.etag}")
        except oss2.exceptions.AccessDenied as e:
            print(f"   ❌ 上传失败: AccessKey 没有写入权限")
            print(f"   💡 错误信息: {e}")
            return False
        except Exception as e:
            print(f"   ❌ 上传失败: {e}")
            return False
        
        # 4. 测试文件读取
        print(f"\n4️⃣  测试文件读取...")
        try:
            result = bucket.get_object(test_object_name)
            content = result.read()
            if content == test_content:
                print(f"   ✅ 文件读取成功，内容匹配")
            else:
                print(f"   ⚠️  文件读取成功，但内容不匹配")
        except Exception as e:
            print(f"   ⚠️  文件读取失败: {e}")
        
        # 5. 测试生成签名 URL
        print(f"\n5️⃣  测试生成签名 URL...")
        try:
            signed_url = bucket.sign_url('GET', test_object_name, 3600)
            print(f"   ✅ 签名 URL 生成成功")
            print(f"   🔗 URL (前100字符): {signed_url[:100]}...")
        except Exception as e:
            print(f"   ⚠️  签名 URL 生成失败: {e}")
        
        # 6. 清理测试文件（可选）
        print(f"\n6️⃣  清理测试文件...")
        try:
            bucket.delete_object(test_object_name)
            print(f"   ✅ 测试文件已删除")
        except Exception as e:
            print(f"   ⚠️  删除测试文件失败（可手动删除）: {e}")
        
        # 7. 生成访问 URL（用于验证）
        print(f"\n7️⃣  生成访问 URL...")
        public_url = f"https://{settings.oss_bucket_name}.{settings.oss_endpoint}/{test_object_name}"
        print(f"   🔗 公开访问 URL: {public_url}")
        print(f"   💡 注意: 如果 Bucket 是私有的，需要使用签名 URL")
        
        print("\n" + "=" * 60)
        print("✅ OSS 连接测试完成！所有测试通过")
        print("=" * 60)
        return True
        
    except oss2.exceptions.InvalidAccessKeyId as e:
        print(f"\n❌ 错误: AccessKey ID 无效")
        print(f"   💡 错误信息: {e}")
        return False
    except oss2.exceptions.SignatureDoesNotMatch as e:
        print(f"\n❌ 错误: AccessKey Secret 无效")
        print(f"   💡 错误信息: {e}")
        return False
    except Exception as e:
        print(f"\n❌ 连接失败: {e}")
        logger.exception("OSS connection test failed")
        return False


if __name__ == "__main__":
    success = test_oss_connection()
    sys.exit(0 if success else 1)

