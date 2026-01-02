#!/usr/bin/env python3
"""
手动测试 process_image 功能
可以直接运行，不依赖 pytest conftest
"""
import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.utils.ai_processor import process_image
from app.schemas.image import ImageOperation, OperationType, SceneType
from app.config import settings
from app.utils.logger import logger


async def test_mock_mode():
    """测试 Mock 模式"""
    print("\n" + "=" * 60)
    print("测试 1: Mock 模式下的图片处理")
    print("=" * 60)
    
    # 使用真实的 OSS 图片地址（带签名）
    image_url = "https://lumina-ai.oss-cn-beijing.aliyuncs.com/user_9c121b41a372/img_90b98f2ab708.jpg?Expires=1767356534&OSSAccessKeyId=TMP.3KmprwjFLxpqXZMZrdVo2LAwF9V8AZJ6V1EFvLZBWCyvqyXwFFvzfZ9Ucvqd4mP89Ni6eo8hxKhwywdVpnzC4uoRexEjoJ&Signature=dkMtxpyxog6wakQDGAVPOeWYgwU%3D"
    operations = [
        ImageOperation(type=OperationType.CUTOUT, params={})
    ]
    
    result = await process_image(
        image_url=image_url,
        operations=operations,
        output_size="2000x2000",
        quality=85,
        scene_type=SceneType.CUSTOM
    )
    
    if result:
        print("✅ Mock 模式测试通过")
        print(f"  processed_url: {result.get('processed_url')}")
        print(f"  thumbnail_url: {result.get('thumbnail_url')}")
        print(f"  width: {result.get('width')}")
        print(f"  height: {result.get('height')}")
        print(f"  size: {result.get('size')}")
        print(f"  format: {result.get('format')}")
    else:
        print("❌ Mock 模式测试失败")


async def test_different_operations():
    """测试不同操作类型"""
    print("\n" + "=" * 60)
    print("测试 2: 不同操作类型")
    print("=" * 60)
    
    # 使用真实的 OSS 图片地址（带签名）
    image_url = "https://lumina-ai.oss-cn-beijing.aliyuncs.com/user_9c121b41a372/img_90b98f2ab708.jpg?Expires=1767356534&OSSAccessKeyId=TMP.3KmprwjFLxpqXZMZrdVo2LAwF9V8AZJ6V1EFvLZBWCyvqyXwFFvzfZ9Ucvqd4mP89Ni6eo8hxKhwywdVpnzC4uoRexEjoJ&Signature=dkMtxpyxog6wakQDGAVPOeWYgwU%3D"
    
    operations_list = [
        [ImageOperation(type=OperationType.CUTOUT, params={})],
        [ImageOperation(type=OperationType.BACKGROUND, params={"backgroundColor": "#FFFFFF"})],
        [ImageOperation(type=OperationType.LIGHTING, params={"brightness": 1.2, "contrast": 1.1})],
        [ImageOperation(type=OperationType.FILTER, params={"filterType": "blur"})],
        [ImageOperation(type=OperationType.RESIZE, params={})],
    ]
    
    operation_names = ["CUTOUT", "BACKGROUND", "LIGHTING", "FILTER", "RESIZE"]
    
    for i, (operations, name) in enumerate(zip(operations_list, operation_names), 1):
        result = await process_image(
            image_url=image_url,
            operations=operations,
            scene_type=SceneType.CUSTOM
        )
        
        if result:
            print(f"✅ {name} 操作测试通过")
        else:
            print(f"❌ {name} 操作测试失败")


async def test_different_scene_types():
    """测试不同场景类型"""
    print("\n" + "=" * 60)
    print("测试 3: 不同场景类型")
    print("=" * 60)
    
    # 使用真实的 OSS 图片地址（带签名）
    image_url = "https://lumina-ai.oss-cn-beijing.aliyuncs.com/user_9c121b41a372/img_90b98f2ab708.jpg?Expires=1767356534&OSSAccessKeyId=TMP.3KmprwjFLxpqXZMZrdVo2LAwF9V8AZJ6V1EFvLZBWCyvqyXwFFvzfZ9Ucvqd4mP89Ni6eo8hxKhwywdVpnzC4uoRexEjoJ&Signature=dkMtxpyxog6wakQDGAVPOeWYgwU%3D"
    operations = [
        ImageOperation(type=OperationType.CUTOUT, params={})
    ]
    
    scene_types = [
        (SceneType.TAOBAO, "淘宝商品"),
        (SceneType.AMAZON, "亚马逊商品"),
        (SceneType.DOUYIN, "抖音"),
        (SceneType.XIAOHONGSHU, "小红书"),
        (SceneType.CUSTOM, "自定义"),
        (None, "未指定"),
    ]
    
    for scene_type, name in scene_types:
        result = await process_image(
            image_url=image_url,
            operations=operations,
            scene_type=scene_type
        )
        
        if result:
            print(f"✅ {name} 场景测试通过")
        else:
            print(f"❌ {name} 场景测试失败")


async def test_multiple_operations():
    """测试多个操作组合"""
    print("\n" + "=" * 60)
    print("测试 4: 多个操作组合")
    print("=" * 60)
    
    # 使用真实的 OSS 图片地址（带签名）
    image_url = "https://lumina-ai.oss-cn-beijing.aliyuncs.com/user_9c121b41a372/img_90b98f2ab708.jpg?Expires=1767356534&OSSAccessKeyId=TMP.3KmprwjFLxpqXZMZrdVo2LAwF9V8AZJ6V1EFvLZBWCyvqyXwFFvzfZ9Ucvqd4mP89Ni6eo8hxKhwywdVpnzC4uoRexEjoJ&Signature=dkMtxpyxog6wakQDGAVPOeWYgwU%3D"
    operations = [
        ImageOperation(type=OperationType.CUTOUT, params={}),
        ImageOperation(type=OperationType.BACKGROUND, params={"backgroundColor": "#FFFFFF"}),
        ImageOperation(type=OperationType.LIGHTING, params={"brightness": 1.2, "contrast": 1.1})
    ]
    
    result = await process_image(
        image_url=image_url,
        operations=operations,
        output_size="2000x2000",
        quality=90,
        scene_type=SceneType.TAOBAO
    )
    
    if result:
        print("✅ 多操作组合测试通过")
        print(f"  操作数量: {len(operations)}")
        print(f"  processed_url: {result.get('processed_url')}")
    else:
        print("❌ 多操作组合测试失败")


async def test_custom_quality_and_size():
    """测试自定义质量和尺寸"""
    print("\n" + "=" * 60)
    print("测试 5: 自定义质量和尺寸")
    print("=" * 60)
    
    # 使用真实的 OSS 图片地址（带签名）
    image_url = "https://lumina-ai.oss-cn-beijing.aliyuncs.com/user_9c121b41a372/img_90b98f2ab708.jpg?Expires=1767356534&OSSAccessKeyId=TMP.3KmprwjFLxpqXZMZrdVo2LAwF9V8AZJ6V1EFvLZBWCyvqyXwFFvzfZ9Ucvqd4mP89Ni6eo8hxKhwywdVpnzC4uoRexEjoJ&Signature=dkMtxpyxog6wakQDGAVPOeWYgwU%3D"
    operations = [
        ImageOperation(type=OperationType.RESIZE, params={})
    ]
    
    test_cases = [
        ("1920x1080", 90),
        ("2000x2000", 85),
        ("1024x768", 95),
    ]
    
    for output_size, quality in test_cases:
        result = await process_image(
            image_url=image_url,
            operations=operations,
            output_size=output_size,
            quality=quality
        )
        
        if result:
            print(f"✅ 尺寸 {output_size}, 质量 {quality} 测试通过")
        else:
            print(f"❌ 尺寸 {output_size}, 质量 {quality} 测试失败")


async def test_configuration_info():
    """显示配置信息"""
    print("\n" + "=" * 60)
    print("配置信息")
    print("=" * 60)
    
    print(f"VIAPI AccessKey ID: {'已设置' if settings.viapi_access_key_id else '未设置'}")
    print(f"VIAPI AccessKey Secret: {'已设置' if settings.viapi_access_key_secret else '未设置'}")
    print(f"VIAPI Mock Mode: {settings.viapi_mock_mode}")
    print(f"VIAPI Region: {settings.viapi_region}")
    print(f"AI Service URL: {settings.ai_service_url or '未设置'}")
    print(f"AI Service Mock Mode: {settings.ai_service_mock_mode}")
    
    if settings.viapi_mock_mode and not settings.ai_service_url:
        print("\n⚠️  当前使用 Mock 模式，将返回模拟的处理结果")
    elif settings.viapi_access_key_id and settings.viapi_access_key_secret and not settings.viapi_mock_mode:
        print("\n✅ 将使用阿里云 VIAPI 进行图片处理")
    elif settings.ai_service_url and not settings.ai_service_mock_mode:
        print("\n✅ 将使用外部 AI 服务进行图片处理")
    
    print("\n" + "=" * 60)
    print("⚠️  重要提示：OSS 图片访问")
    print("=" * 60)
    print("如果测试失败并出现 403 错误，可能的原因：")
    print("1. OSS 签名 URL 已过期（签名 URL 通常有时效性）")
    print("2. OSS bucket 是私有的，需要使用带签名的 URL")
    print("3. 临时凭证（TMP.）可能已失效")
    print("\n建议：")
    print("- 使用 Mock 模式进行功能测试（设置 VIAPI_MOCK_MODE=true）")
    print("- 或者使用 storage_service 生成新的签名 URL")
    print("- 或者将 OSS bucket 设置为公共读（不推荐生产环境）")


async def main():
    """运行所有测试"""
    print("\n" + "=" * 60)
    print("process_image 功能测试")
    print("=" * 60)
    
    # 显示配置信息
    await test_configuration_info()
    
    # 运行测试
    await test_mock_mode()
    await test_different_operations()
    await test_different_scene_types()
    await test_multiple_operations()
    await test_custom_quality_and_size()
    
    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

