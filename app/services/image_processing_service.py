"""
阿里云视觉智能开放平台图像处理服务
支持：抠图、背景替换、图像增强、打光、阴影等
"""
import httpx
import base64
from typing import Optional, Dict, Any, List
from app.config import settings
from app.schemas.image import ImageOperation, OperationType
from app.utils.logger import logger
from app.services.storage_service import storage_service


async def _download_image_as_bytes(image_url: str) -> Optional[bytes]:
    """下载图片并转换为 bytes"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                logger.error(f"Failed to download image from {image_url}: {response.status_code}")
                return None
            return response.content
    except Exception as e:
        logger.error(f"Error downloading image: {e}", exc_info=True)
        return None


async def _segment_image(
    image_bytes: bytes,
    scene_type: Optional[str] = None,
    image_url: Optional[str] = None
) -> Optional[bytes]:
    """
    使用阿里云视觉智能开放平台进行图像分割（抠图）
    智能选择最合适的分割服务：
    - 商品场景（taobao, amazon）→ 商品分割
    - 人像场景 → 人体分割
    - 其他场景 → 通用分割
    
    Args:
        image_bytes: 图片字节数据
        scene_type: 场景类型（taobao, amazon, douyin, xiaohongshu, custom）
        image_url: 图片 URL（可选，用于 AI 分析图片类型）
    
    Returns:
        分割后的透明背景 PNG 图片 bytes
    """
    if settings.viapi_mock_mode or not (settings.viapi_access_key_id and settings.viapi_access_key_secret):
        logger.debug("VIAPI mock mode: returning mock segmented image")
        return image_bytes  # Mock: 返回原图
    
    try:
        from alibabacloud_imageseg20191230.client import Client as ImagesegClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_imageseg20191230 import models as imageseg_models
        
        # 初始化客户端
        config = open_api_models.Config(
            access_key_id=settings.viapi_access_key_id,
            access_key_secret=settings.viapi_access_key_secret,
            region_id=settings.viapi_region,
            endpoint=f"imageseg.{settings.viapi_region}.aliyuncs.com"
        )
        client = ImagesegClient(config)
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 智能选择分割服务
        segmentation_method = "common"  # 默认使用通用分割
        
        # 根据场景类型选择
        if scene_type:
            scene_lower = scene_type.lower()
            if scene_lower in ["taobao", "amazon"]:
                segmentation_method = "commodity"  # 商品分割
                logger.debug(f"根据场景类型 {scene_type} 选择商品分割服务")
            elif scene_lower in ["douyin", "xiaohongshu"]:
                # 短视频平台可能包含人像，但不确定，先尝试通用分割
                # 如果需要更精确，可以使用 AI 分析
                segmentation_method = "common"
                logger.debug(f"根据场景类型 {scene_type} 使用通用分割服务")
        
        # 如果提供了图片 URL，可以使用通义千问 VL 分析图片类型（可选）
        # 这里先使用场景类型判断，后续可以增强为 AI 分析
        
        # 根据选择的方法调用不同的 API
        response = None
        
        if segmentation_method == "commodity":
            # 使用商品分割
            try:
                request = imageseg_models.SegmentCommodityRequest(
                    image_url=None,
                    return_form="png"
                )
                request.body = image_base64
                response = client.segment_commodity(request)
                logger.debug("使用商品分割服务")
            except Exception as e:
                logger.warning(f"商品分割失败，降级到通用分割: {e}")
                segmentation_method = "common"
        
        if segmentation_method == "common" or response is None:
            # 使用通用分割
            request = imageseg_models.SegmentCommonImageRequest(
                image_url=None,
                return_form="png"  # 返回 PNG 格式（支持透明背景）
            )
            request.body = image_base64
            response = client.segment_common_image(request)
            logger.debug("使用通用分割服务")
        
        # 处理响应
        if response and response.body.data:
            # 如果返回图片 URL
            if hasattr(response.body.data, 'image_url') and response.body.data.image_url:
                # 检查是否是 URL 还是 base64
                if response.body.data.image_url.startswith('http'):
                    # 下载分割后的图片
                    async with httpx.AsyncClient(timeout=30.0) as http_client:
                        img_response = await http_client.get(response.body.data.image_url)
                        if img_response.status_code == 200:
                            return img_response.content
                else:
                    # 可能是 base64 数据
                    try:
                        return base64.b64decode(response.body.data.image_url)
                    except:
                        pass
            
            # 如果返回 base64 字段
            if hasattr(response.body.data, 'image_data') and response.body.data.image_data:
                try:
                    return base64.b64decode(response.body.data.image_data)
                except:
                    pass
        
        logger.warning("Image segmentation returned no valid result")
        return None
        
    except ImportError:
        logger.error("阿里云视觉智能开放平台 SDK 未安装。请安装: pip install alibabacloud-imageseg20191230")
        return None
    except Exception as e:
        logger.error(f"Image segmentation error: {e}", exc_info=True)
        return None


async def _replace_background(
    image_bytes: bytes,
    background_color: str = "#FFFFFF",
    scene_type: Optional[str] = None,
    image_url: Optional[str] = None
) -> Optional[bytes]:
    """
    替换背景（基于分割结果 + 纯色背景）
    
    Args:
        image_bytes: 图片字节数据
        background_color: 背景颜色
        scene_type: 场景类型（用于智能选择分割服务）
        image_url: 图片 URL（可选）
    """
    # 先进行分割（使用智能选择）
    segmented = await _segment_image(image_bytes, scene_type, image_url)
    if not segmented:
        return None
    
    # 使用 PIL 将分割结果与背景色合成
    try:
        from PIL import Image, ImageColor
        import io
        
        # 打开分割后的图片（应该是透明背景 PNG）
        foreground = Image.open(io.BytesIO(segmented)).convert("RGBA")
        
        # 创建背景图片
        bg_color_rgba = ImageColor.getcolor(background_color, "RGB") + (255,)
        background = Image.new("RGBA", foreground.size, bg_color_rgba)
        
        # 合成图片
        result = Image.alpha_composite(background, foreground)
        
        # 转换为 RGB（移除 alpha 通道）
        result = result.convert("RGB")
        
        # 转换为 bytes
        output = io.BytesIO()
        result.save(output, format="JPEG", quality=95)
        return output.getvalue()
        
    except Exception as e:
        logger.error(f"Background replacement error: {e}", exc_info=True)
        # 如果合成失败，返回分割结果
        return segmented


async def _enhance_lighting(image_bytes: bytes, brightness: float = 1.0, contrast: float = 1.0) -> Optional[bytes]:
    """
    调整光线（亮度、对比度）
    优先使用阿里云图像生产服务，其次图像增强服务，最后本地 PIL 处理
    """
    if settings.viapi_mock_mode:
        # 使用本地 PIL 处理
        try:
            from PIL import Image, ImageEnhance
            import io
            
            img = Image.open(io.BytesIO(image_bytes))
            
            # 调整亮度
            if brightness != 1.0:
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(brightness)
            
            # 调整对比度
            if contrast != 1.0:
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(contrast)
            
            # 转换为 bytes
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=95)
            return output.getvalue()
        except Exception as e:
            logger.error(f"Local lighting enhancement error: {e}", exc_info=True)
            return image_bytes
    
    # 优先使用阿里云图像生产服务（图像属性增强）
    try:
        from alibabacloud_imageprocess20200320.client import Client as ImageprocessClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_imageprocess20200320 import models as imageprocess_models
        
        config = open_api_models.Config(
            access_key_id=settings.viapi_access_key_id,
            access_key_secret=settings.viapi_access_key_secret,
            region_id=settings.viapi_region,
            endpoint=f"imageprocess.{settings.viapi_region}.aliyuncs.com"
        )
        client = ImageprocessClient(config)
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 使用图像属性增强 API（支持曝光矫正、色彩矫正）
        # 根据 brightness 和 contrast 参数调整
        request = imageprocess_models.AdvanceImageEnhanceRequest(
            image_url=None,
            mode="auto"  # 自动增强模式
        )
        request.body = image_base64
        
        response = client.advance_image_enhance(request)
        
        if response.body.data and response.body.data.image_url:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                img_response = await http_client.get(response.body.data.image_url)
                if img_response.status_code == 200:
                    enhanced_bytes = img_response.content
                    # 如果还需要进一步调整亮度/对比度，使用本地处理
                    if brightness != 1.0 or contrast != 1.0:
                        return await _enhance_lighting(enhanced_bytes, brightness, contrast)
                    return enhanced_bytes
        
    except ImportError:
        logger.debug("图像生产服务 SDK 未安装，尝试使用图像增强服务")
    except Exception as e:
        logger.debug(f"图像生产服务调用失败: {e}，尝试使用图像增强服务")
    
    # 降级使用阿里云图像增强服务
    try:
        from alibabacloud_imageenhan20190930.client import Client as ImageenhanClient
        from alibabacloud_tea_openapi import models as open_api_models
        from alibabacloud_imageenhan20190930 import models as imageenhan_models
        
        config = open_api_models.Config(
            access_key_id=settings.viapi_access_key_id,
            access_key_secret=settings.viapi_access_key_secret,
            region_id=settings.viapi_region,
            endpoint=f"imageenhan.{settings.viapi_region}.aliyuncs.com"
        )
        client = ImageenhanClient(config)
        
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        request = imageenhan_models.EnhanceImageRequest(
            image_url=None,
            mode="auto"  # 自动增强
        )
        request.body = image_base64
        
        response = client.enhance_image(request)
        
        if response.body.data and response.body.data.image_url:
            async with httpx.AsyncClient(timeout=30.0) as http_client:
                img_response = await http_client.get(response.body.data.image_url)
                if img_response.status_code == 200:
                    enhanced_bytes = img_response.content
                    # 如果还需要进一步调整亮度/对比度，使用本地处理
                    if brightness != 1.0 or contrast != 1.0:
                        return await _enhance_lighting(enhanced_bytes, brightness, contrast)
                    return enhanced_bytes
        
    except Exception as e:
        logger.debug(f"图像增强服务调用失败: {e}，使用本地处理")
    
    # 最终降级到本地处理
    return await _enhance_lighting(image_bytes, brightness, contrast)


async def process_image_with_viapi(
    image_url: str,
    operations: List[ImageOperation],
    output_size: Optional[str] = None,
    quality: int = 85,
    scene_type: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    使用阿里云视觉智能开放平台处理图片
    
    Args:
        image_url: 原始图片 URL
        operations: 处理操作列表
        output_size: 输出尺寸（如 "2000x2000"）
        quality: 输出质量（60-100）
        scene_type: 场景类型（用于智能选择分割服务）
    
    Returns:
        处理结果字典，包含 processed_url, thumbnail_url 等
    """
    # 下载原始图片
    image_bytes = await _download_image_as_bytes(image_url)
    if not image_bytes:
        logger.error(f"Failed to download image from {image_url}")
        return None
    
    processed_bytes = image_bytes
    
    # 按顺序执行操作
    for operation in operations:
        op_type = operation.type
        params = operation.params or {}
        
        try:
            if op_type == OperationType.CUTOUT:
                # 抠图（使用智能选择）
                processed_bytes = await _segment_image(processed_bytes, scene_type, image_url)
                if not processed_bytes:
                    logger.warning("Image segmentation failed, skipping")
                    continue
            
            elif op_type == OperationType.BACKGROUND:
                # 背景处理（使用智能选择）
                bg_color = params.get("backgroundColor", "#FFFFFF")
                processed_bytes = await _replace_background(processed_bytes, bg_color, scene_type, image_url)
                if not processed_bytes:
                    logger.warning("Background replacement failed, skipping")
                    continue
            
            elif op_type == OperationType.LIGHTING:
                # 打光
                brightness = params.get("brightness", 1.0)
                contrast = params.get("contrast", 1.0)
                processed_bytes = await _enhance_lighting(processed_bytes, brightness, contrast)
                if not processed_bytes:
                    logger.warning("Lighting enhancement failed, skipping")
                    continue
            
            elif op_type == OperationType.FILTER:
                # 滤镜（使用本地 PIL 处理）
                try:
                    from PIL import Image, ImageFilter
                    import io
                    
                    img = Image.open(io.BytesIO(processed_bytes))
                    filter_type = params.get("filterType", "none")
                    
                    if filter_type == "blur":
                        img = img.filter(ImageFilter.BLUR)
                    elif filter_type == "sharpen":
                        img = img.filter(ImageFilter.SHARPEN)
                    elif filter_type == "smooth":
                        img = img.filter(ImageFilter.SMOOTH)
                    
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=quality)
                    processed_bytes = output.getvalue()
                except Exception as e:
                    logger.error(f"Filter application error: {e}", exc_info=True)
            
            elif op_type == OperationType.RESIZE:
                # 调整大小
                try:
                    from PIL import Image
                    import io
                    
                    img = Image.open(io.BytesIO(processed_bytes))
                    if output_size:
                        width, height = map(int, output_size.split('x'))
                        img = img.resize((width, height), Image.Resampling.LANCZOS)
                    
                    output = io.BytesIO()
                    img.save(output, format="JPEG", quality=quality)
                    processed_bytes = output.getvalue()
                except Exception as e:
                    logger.error(f"Resize error: {e}", exc_info=True)
        
        except Exception as e:
            logger.error(f"Error processing operation {op_type}: {e}", exc_info=True)
            continue
    
    if not processed_bytes:
        logger.error("All image processing operations failed")
        return None
    
    # 上传处理后的图片到 OSS
    try:
        # 生成文件路径
        import uuid
        from datetime import datetime
        file_id = uuid.uuid4().hex[:12]
        file_path = f"processed/{datetime.now().strftime('%Y%m%d')}/{file_id}.jpg"
        
        # 上传到 OSS
        processed_url = storage_service.upload_file(
            processed_bytes,
            file_path,
            content_type="image/jpeg"
        )
        
        # 生成缩略图
        thumbnail_bytes = storage_service.generate_thumbnail(processed_bytes)
        thumbnail_path = f"processed/{datetime.now().strftime('%Y%m%d')}/thumb_{file_id}.jpg"
        thumbnail_url = storage_service.upload_file(
            thumbnail_bytes,
            thumbnail_path,
            content_type="image/jpeg"
        )
        
        # 获取图片尺寸
        from PIL import Image
        import io
        img = Image.open(io.BytesIO(processed_bytes))
        width, height = img.size
        
        return {
            "processed_url": processed_url,
            "thumbnail_url": thumbnail_url,
            "width": width,
            "height": height,
            "size": len(processed_bytes),
            "format": "jpg"
        }
    
    except Exception as e:
        logger.error(f"Error uploading processed image: {e}", exc_info=True)
        return None

