"""
测试 process_image 功能
"""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from app.utils.ai_processor import process_image
from app.schemas.image import ImageOperation, OperationType, SceneType
from app.config import settings


class TestProcessImage:
    """测试 process_image 函数"""

    @pytest.mark.asyncio
    async def test_process_image_mock_mode(self):
        """测试 Mock 模式下的图片处理"""
        # 设置 mock 模式
        with patch.object(settings, 'viapi_access_key_id', None), \
             patch.object(settings, 'viapi_access_key_secret', None), \
             patch.object(settings, 'viapi_mock_mode', True), \
             patch.object(settings, 'ai_service_url', None), \
             patch.object(settings, 'ai_service_mock_mode', True):

            image_url = "http://example.com/uploads/test.jpg"
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

            assert result is not None
            assert "processed_url" in result
            assert "thumbnail_url" in result
            assert result["width"] == 2000
            assert result["height"] == 2000
            assert result["size"] == 1536000
            assert result["format"] == "jpg"
            # 验证 URL 转换
            assert "/processed/" in result["processed_url"]
            assert "/uploads/" not in result["processed_url"]

    @pytest.mark.asyncio
    async def test_process_image_with_viapi_success(self):
        """测试使用 VIAPI 处理图片（成功）"""
        mock_result = {
            "processed_url": "https://example.com/processed/test.jpg",
            "thumbnail_url": "https://example.com/processed/thumb_test.jpg",
            "width": 2000,
            "height": 2000,
            "size": 1536000,
            "format": "jpg"
        }

        with patch.object(settings, 'viapi_access_key_id', "test_key"), \
             patch.object(settings, 'viapi_access_key_secret', "test_secret"), \
             patch.object(settings, 'viapi_mock_mode', False):

            with patch('app.utils.ai_processor.process_image_with_viapi') as mock_viapi:
                mock_viapi.return_value = mock_result

                image_url = "http://example.com/uploads/test.jpg"
                operations = [
                    ImageOperation(type=OperationType.CUTOUT, params={})
                ]

                result = await process_image(
                    image_url=image_url,
                    operations=operations,
                    scene_type=SceneType.TAOBAO
                )

                assert result == mock_result
                # 验证调用了 VIAPI 服务
                mock_viapi.assert_called_once_with(
                    image_url,
                    operations,
                    None,  # output_size
                    85,    # quality
                    SceneType.TAOBAO  # scene_type
                )

    @pytest.mark.asyncio
    async def test_process_image_with_viapi_failure_fallback(self):
        """测试 VIAPI 失败时降级到外部服务"""
        with patch.object(settings, 'viapi_access_key_id', "test_key"), \
             patch.object(settings, 'viapi_access_key_secret', "test_secret"), \
             patch.object(settings, 'viapi_mock_mode', False), \
             patch.object(settings, 'ai_service_url', "https://external-ai.com/process"), \
             patch.object(settings, 'ai_service_mock_mode', False), \
             patch.object(settings, 'ai_service_api_key', "test_api_key"):

            # VIAPI 抛出异常
            with patch('app.utils.ai_processor.process_image_with_viapi') as mock_viapi:
                mock_viapi.side_effect = Exception("VIAPI error")

                # Mock 外部 AI 服务响应
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = {
                    "processed_url": "https://external.com/processed.jpg",
                    "width": 1920,
                    "height": 1080
                }

                with patch('httpx.AsyncClient') as mock_client:
                    mock_client_instance = AsyncMock()
                    mock_client_instance.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
                    mock_client.return_value = mock_client_instance

                    image_url = "http://example.com/uploads/test.jpg"
                    operations = [
                        ImageOperation(type=OperationType.CUTOUT, params={})
                    ]

                    result = await process_image(
                        image_url=image_url,
                        operations=operations
                    )

                    assert result is not None
                    assert result["processed_url"] == "https://external.com/processed.jpg"

    @pytest.mark.asyncio
    async def test_process_image_external_service_success(self):
        """测试外部 AI 服务处理图片（成功）"""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "processed_url": "https://external.com/processed.jpg",
            "thumbnail_url": "https://external.com/thumb.jpg",
            "width": 1920,
            "height": 1080,
            "size": 1000000,
            "format": "png"
        }

        with patch.object(settings, 'viapi_access_key_id', None), \
             patch.object(settings, 'viapi_access_key_secret', None), \
             patch.object(settings, 'viapi_mock_mode', True), \
             patch.object(settings, 'ai_service_url', "https://external-ai.com/process"), \
             patch.object(settings, 'ai_service_mock_mode', False), \
             patch.object(settings, 'ai_service_api_key', "test_api_key"):

            with patch('httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_post = AsyncMock(return_value=mock_response)
                mock_client_instance.__aenter__.return_value.post = mock_post
                mock_client.return_value = mock_client_instance

                image_url = "http://example.com/uploads/test.jpg"
                operations = [
                    ImageOperation(type=OperationType.BACKGROUND, params={"backgroundColor": "#FFFFFF"})
                ]

                result = await process_image(
                    image_url=image_url,
                    operations=operations,
                    output_size="1920x1080",
                    quality=90
                )

                assert result is not None
                assert result["processed_url"] == "https://external.com/processed.jpg"
                # 验证请求参数
                mock_post.assert_called_once()
                call_args = mock_post.call_args
                assert call_args[1]["json"]["image_url"] == image_url
                assert call_args[1]["json"]["operations"][0]["type"] == "background"
                assert call_args[1]["json"]["output_size"] == "1920x1080"
                assert call_args[1]["json"]["quality"] == 90
                assert "Authorization" in call_args[1]["headers"]
                assert call_args[1]["headers"]["Authorization"] == "Bearer test_api_key"

    @pytest.mark.asyncio
    async def test_process_image_external_service_failure_fallback_to_mock(self):
        """测试外部服务失败时降级到 Mock 模式"""
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_response.text = "Internal Server Error"

        with patch.object(settings, 'viapi_access_key_id', None), \
             patch.object(settings, 'viapi_access_key_secret', None), \
             patch.object(settings, 'viapi_mock_mode', True), \
             patch.object(settings, 'ai_service_url', "https://external-ai.com/process"), \
             patch.object(settings, 'ai_service_mock_mode', False):

            with patch('httpx.AsyncClient') as mock_client:
                mock_client_instance = AsyncMock()
                mock_post = AsyncMock(return_value=mock_response)
                mock_client_instance.__aenter__.return_value.post = mock_post
                mock_client.return_value = mock_client_instance

                image_url = "http://example.com/uploads/test.jpg"
                operations = [
                    ImageOperation(type=OperationType.LIGHTING, params={"brightness": 1.2})
                ]

                result = await process_image(
                    image_url=image_url,
                    operations=operations
                )

                # 应该降级到 Mock 模式
                assert result is not None
                assert "processed_url" in result
                assert result["width"] == 2000
                assert result["height"] == 2000

    @pytest.mark.asyncio
    async def test_process_image_with_different_scene_types(self):
        """测试不同场景类型的处理"""
        mock_result = {
            "processed_url": "https://example.com/processed/test.jpg",
            "thumbnail_url": "https://example.com/processed/thumb_test.jpg",
            "width": 2000,
            "height": 2000,
            "size": 1536000,
            "format": "jpg"
        }

        with patch.object(settings, 'viapi_access_key_id', "test_key"), \
             patch.object(settings, 'viapi_access_key_secret', "test_secret"), \
             patch.object(settings, 'viapi_mock_mode', False):

            with patch('app.utils.ai_processor.process_image_with_viapi') as mock_viapi:
                mock_viapi.return_value = mock_result

                image_url = "http://example.com/uploads/test.jpg"
                operations = [
                    ImageOperation(type=OperationType.CUTOUT, params={})
                ]

                # 测试不同场景类型
                scene_types = [
                    SceneType.TAOBAO,
                    SceneType.AMAZON,
                    SceneType.DOUYIN,
                    SceneType.XIAOHONGSHU,
                    SceneType.CUSTOM,
                    None
                ]

                for scene_type in scene_types:
                    result = await process_image(
                        image_url=image_url,
                        operations=operations,
                        scene_type=scene_type
                    )

                    assert result == mock_result
                    # 验证 scene_type 被正确传递
                    call_args = mock_viapi.call_args
                    assert call_args[0][4] == scene_type  # scene_type 是第5个参数

    @pytest.mark.asyncio
    async def test_process_image_with_multiple_operations(self):
        """测试多个操作的处理"""
        mock_result = {
            "processed_url": "https://example.com/processed/test.jpg",
            "thumbnail_url": "https://example.com/processed/thumb_test.jpg",
            "width": 2000,
            "height": 2000,
            "size": 1536000,
            "format": "jpg"
        }

        with patch.object(settings, 'viapi_access_key_id', "test_key"), \
             patch.object(settings, 'viapi_access_key_secret', "test_secret"), \
             patch.object(settings, 'viapi_mock_mode', False):

            with patch('app.utils.ai_processor.process_image_with_viapi') as mock_viapi:
                mock_viapi.return_value = mock_result

                image_url = "http://example.com/uploads/test.jpg"
                operations = [
                    ImageOperation(type=OperationType.CUTOUT, params={}),
                    ImageOperation(type=OperationType.BACKGROUND, params={"backgroundColor": "#FFFFFF"}),
                    ImageOperation(type=OperationType.LIGHTING, params={"brightness": 1.2, "contrast": 1.1})
                ]

                result = await process_image(
                    image_url=image_url,
                    operations=operations,
                    output_size="2000x2000",
                    quality=90
                )

                assert result == mock_result
                # 验证所有操作都被传递
                call_args = mock_viapi.call_args
                assert len(call_args[0][1]) == 3  # operations 列表长度

    @pytest.mark.asyncio
    async def test_process_image_all_operation_types(self):
        """测试所有操作类型"""
        mock_result = {
            "processed_url": "https://example.com/processed/test.jpg",
            "thumbnail_url": "https://example.com/processed/thumb_test.jpg",
            "width": 2000,
            "height": 2000,
            "size": 1536000,
            "format": "jpg"
        }

        with patch.object(settings, 'viapi_access_key_id', "test_key"), \
             patch.object(settings, 'viapi_access_key_secret', "test_secret"), \
             patch.object(settings, 'viapi_mock_mode', False):

            with patch('app.utils.ai_processor.process_image_with_viapi') as mock_viapi:
                mock_viapi.return_value = mock_result

                image_url = "http://example.com/uploads/test.jpg"

                # 测试所有操作类型
                operation_types = [
                    OperationType.CUTOUT,
                    OperationType.BACKGROUND,
                    OperationType.LIGHTING,
                    OperationType.FILTER,
                    OperationType.RESIZE
                ]

                for op_type in operation_types:
                    operations = [ImageOperation(type=op_type, params={})]

                    result = await process_image(
                        image_url=image_url,
                        operations=operations
                    )

                    assert result == mock_result

    @pytest.mark.asyncio
    async def test_process_image_with_custom_quality_and_size(self):
        """测试自定义质量和尺寸"""
        mock_result = {
            "processed_url": "https://example.com/processed/test.jpg",
            "thumbnail_url": "https://example.com/processed/thumb_test.jpg",
            "width": 1920,
            "height": 1080,
            "size": 1000000,
            "format": "jpg"
        }

        with patch.object(settings, 'viapi_access_key_id', "test_key"), \
             patch.object(settings, 'viapi_access_key_secret', "test_secret"), \
             patch.object(settings, 'viapi_mock_mode', False):

            with patch('app.utils.ai_processor.process_image_with_viapi') as mock_viapi:
                mock_viapi.return_value = mock_result

                image_url = "http://example.com/uploads/test.jpg"
                operations = [
                    ImageOperation(type=OperationType.RESIZE, params={})
                ]

                result = await process_image(
                    image_url=image_url,
                    operations=operations,
                    output_size="1920x1080",
                    quality=95,
                    edge_smoothing=False
                )

                assert result == mock_result
                # 验证参数被正确传递
                call_args = mock_viapi.call_args
                assert call_args[0][2] == "1920x1080"  # output_size
                assert call_args[0][3] == 95  # quality

    @pytest.mark.asyncio
    async def test_process_image_viapi_import_error_fallback(self):
        """测试 VIAPI 导入错误时降级"""
        with patch.object(settings, 'viapi_access_key_id', "test_key"), \
             patch.object(settings, 'viapi_access_key_secret', "test_secret"), \
             patch.object(settings, 'viapi_mock_mode', False), \
             patch.object(settings, 'ai_service_url', None):

            # 模拟 ImportError
            with patch('app.utils.ai_processor.process_image_with_viapi', side_effect=ImportError("Module not found")):
                image_url = "http://example.com/uploads/test.jpg"
                operations = [
                    ImageOperation(type=OperationType.CUTOUT, params={})
                ]

                result = await process_image(
                    image_url=image_url,
                    operations=operations
                )

                # 应该降级到 Mock 模式
                assert result is not None
                assert "processed_url" in result
                assert result["width"] == 2000

