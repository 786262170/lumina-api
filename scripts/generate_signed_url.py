#!/usr/bin/env python3
"""
为已存在的 OSS 文件生成签名 URL
用于修复之前上传的文件无法访问的问题
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.services.storage_service import storage_service
from app.config import settings


def generate_signed_url(file_path: str, expires: int = 31536000):
    """
    为文件生成签名 URL
    
    Args:
        file_path: OSS 文件路径，例如: user_9c121b41a372/img_898a32f54e51.jpg
        expires: URL 有效期（秒），默认 1 年 (31536000)
    
    Returns:
        签名 URL
    """
    if settings.oss_mock_mode:
        print("⚠️  OSS 处于 mock 模式，返回本地 URL")
        if settings.static_domain:
            return f"https://{settings.static_domain.rstrip('/')}/{settings.oss_local_storage_path}/{file_path}"
        else:
            return f"{settings.base_url.rstrip('/')}/{settings.oss_local_storage_path}/{file_path}"
    
    try:
        signed_url = storage_service.get_signed_url(file_path, expires)
        return signed_url
    except Exception as e:
        print(f"❌ 生成签名 URL 失败: {e}")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/generate_signed_url.py <file_path> [expires_seconds]")
        print("示例: python scripts/generate_signed_url.py user_9c121b41a372/img_898a32f54e51.jpg")
        print("示例: python scripts/generate_signed_url.py user_9c121b41a372/img_898a32f54e51.jpg 3600")
        sys.exit(1)
    
    file_path = sys.argv[1]
    expires = int(sys.argv[2]) if len(sys.argv) > 2 else 31536000
    
    print("=" * 60)
    print("生成 OSS 文件签名 URL")
    print("=" * 60)
    print(f"\n📄 文件路径: {file_path}")
    print(f"⏰ 有效期: {expires} 秒 ({expires // 86400} 天)")
    
    signed_url = generate_signed_url(file_path, expires)
    
    if signed_url:
        print(f"\n✅ 签名 URL 生成成功:")
        print(f"🔗 {signed_url}")
        print(f"\n💡 提示: 将此 URL 复制到浏览器中即可访问文件")
    else:
        print("\n❌ 生成失败")
        sys.exit(1)

