#!/usr/bin/env python3
"""
测试阿里云视觉智能开放平台连接
"""
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.config import settings
from app.utils.logger import logger


def test_viapi_config():
    """测试 VIAPI 配置"""
    print("=" * 60)
    print("测试阿里云视觉智能开放平台配置")
    print("=" * 60)
    
    # 显示配置信息
    print(f"\n📋 配置信息：")
    print(f"  AccessKey ID: {settings.viapi_access_key_id[:10] if settings.viapi_access_key_id else 'None'}...{settings.viapi_access_key_id[-4:] if settings.viapi_access_key_id else ''}")
    print(f"  AccessKey Secret: {'***' if settings.viapi_access_key_secret else '(未设置)'}")
    print(f"  Region: {settings.viapi_region}")
    print(f"  Mock Mode: {settings.viapi_mock_mode}")
    
    if settings.viapi_mock_mode:
        print("\n⚠️  警告: VIAPI_MOCK_MODE 为 true，将使用本地处理，不会连接到真实的 VIAPI")
        return False
    
    if not settings.viapi_access_key_id or not settings.viapi_access_key_secret:
        print("\n❌ 错误: AccessKey ID 或 Secret 未配置")
        return False
    
    print("\n✅ 配置检查通过！")
    print("\n💡 提示：")
    print("   1. 确保已在控制台开通'分割抠图'服务")
    print("   2. 确保已在控制台开通'图像生产'服务（推荐）")
    print("   3. 确保 AccessKey 有相应权限")
    
    return True


def test_llm_config():
    """测试 LLM 配置"""
    print("\n" + "=" * 60)
    print("测试通义千问 VL 配置")
    print("=" * 60)
    
    # 显示配置信息
    print(f"\n📋 配置信息：")
    print(f"  Provider: {settings.llm_provider}")
    print(f"  Model: {settings.llm_model}")
    print(f"  API Key: {'***' if settings.llm_api_key else '(未设置)'}")
    print(f"  Base URL: {settings.llm_base_url or '(默认)'}")
    print(f"  Mock Mode: {settings.llm_mock_mode}")
    
    if settings.llm_mock_mode:
        print("\n⚠️  警告: LLM_MOCK_MODE 为 true，将返回模拟结果")
    
    if not settings.llm_api_key:
        print("\n❌ 错误: LLM_API_KEY 未配置")
        print("\n💡 如何获取 DashScope API Key：")
        print("   1. 访问 https://dashscope.console.aliyun.com/")
        print("   2. 点击左侧菜单'API-KEY 管理'")
        print("   3. 点击'创建新的 API Key'")
        print("   4. 复制生成的 API Key（格式：sk-xxxxxxxxxxxxx）")
        print("   5. 在 .env 文件中配置：LLM_API_KEY=sk-your-api-key")
        return False
    
    print("\n✅ 配置检查通过！")
    return True


if __name__ == "__main__":
    viapi_ok = test_viapi_config()
    llm_ok = test_llm_config()
    
    print("\n" + "=" * 60)
    if viapi_ok and llm_ok:
        print("✅ 所有配置检查通过！")
    else:
        print("⚠️  部分配置需要完善")
        if not viapi_ok:
            print("   - 视觉智能开放平台配置需要完善")
        if not llm_ok:
            print("   - 通义千问 VL 配置需要完善")
    print("=" * 60)
    
    sys.exit(0 if (viapi_ok and llm_ok) else 1)

