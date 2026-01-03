import oss2
from typing import Optional, Tuple
from PIL import Image
import io
import os
import time
from pathlib import Path
from app.config import settings
from app.utils.logger import logger


class StorageService:
    def __init__(self):
        self.mock_mode = settings.oss_mock_mode or not (settings.oss_access_key_id and settings.oss_access_key_secret)
        
        if not self.mock_mode:
            auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
            # 配置 OSS 连接参数：增加超时时间
            # 注意：oss2.Bucket 只支持 connect_timeout，不支持 read_timeout
            self.bucket = oss2.Bucket(
                auth, 
                settings.oss_endpoint, 
                settings.oss_bucket_name,
                connect_timeout=30  # 连接超时 30 秒
            )
        else:
            self.bucket = None
            # Create local storage directory if it doesn't exist
            self.local_storage_path = Path(settings.oss_local_storage_path)
            self.local_storage_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"OSS mock mode enabled. Local storage path: {self.local_storage_path.absolute()}")
    
    def upload_file(
        self,
        file_content: bytes,
        file_path: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload file to OSS or local filesystem (mock mode)
        Returns: file URL
        """
        if self.mock_mode:
            # Mock mode: save to local filesystem
            local_file_path = self.local_storage_path / file_path
            # Create parent directories if they don't exist
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write file to local filesystem
            with open(local_file_path, 'wb') as f:
                f.write(file_content)
            
            # Return full URL with base URL prefix
            # Use static_domain if configured, otherwise use base_url
            if settings.static_domain:
                url = f"https://{settings.static_domain.rstrip('/')}/{settings.oss_local_storage_path}/{file_path}"
            else:
                url = f"{settings.base_url.rstrip('/')}/{settings.oss_local_storage_path}/{file_path}"
            logger.debug(f"File saved to local storage: {local_file_path}, URL: {url}")
            return url
        
        # Real OSS mode with retry mechanism
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                self.bucket.put_object(file_path, file_content, headers={"Content-Type": content_type})
                # Generate signed URL for private bucket access (expires in 1 year)
                # This ensures files can be accessed even if bucket is private
                url = self.bucket.sign_url('GET', file_path, 31536000)  # 1 year = 31536000 seconds
                logger.debug(f"File uploaded to OSS: {file_path}, signed URL generated")
                return url
            except (ConnectionError, oss2.exceptions.RequestError) as e:
                # 网络连接错误，可以重试
                if attempt < max_retries - 1:
                    wait_time = retry_delay * (attempt + 1)  # 指数退避
                    logger.warning(f"OSS upload failed (attempt {attempt + 1}/{max_retries}): {e}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"OSS upload error after {max_retries} attempts: {e}", exc_info=True)
                    raise
            except Exception as e:
                # 其他错误，不重试
                logger.error(f"OSS upload error: {e}", exc_info=True)
                raise
    
    def upload_file_to_viapi_region(
        self,
        file_content: bytes,
        file_path: str,
        content_type: str = "image/jpeg"
    ) -> Optional[str]:
        """
        使用 FileUtils 上传文件到 viapi 的 region（确保地域一致）
        如果 FileUtils 不可用，降级到普通 OSS 上传
        """
        # 如果 viapi 未配置，使用普通上传
        if not settings.viapi_access_key_id or not settings.viapi_access_key_secret:
            logger.warning(f"viapi 未配置，使用普通 OSS 上传（region: {settings.oss_region}），可能与 viapi region ({settings.viapi_region}) 不匹配")
            return self.upload_file(file_content, file_path, content_type)
        
        # 尝试使用 FileUtils 上传到 viapi 的 region
        try:
            from viapi.fileutils import FileUtils
            import tempfile
            
            file_utils = FileUtils(
                settings.viapi_access_key_id,
                settings.viapi_access_key_secret
            )
            
            # 检测图片格式
            img_format = "jpg"
            suffix = ".jpg"
            if file_content[:8] == b'\x89PNG\r\n\x1a\n':
                img_format = "png"
                suffix = ".png"
            
            # FileUtils 需要文件路径，先保存为临时文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
                tmp_file.write(file_content)
                tmp_file_path = tmp_file.name
            
            try:
                # 上传图片并获取 OSS URL（自动处理地域问题）
                oss_url = file_utils.get_oss_url(tmp_file_path, img_format, True)
                logger.debug(f"使用 FileUtils 上传到 viapi region 成功: {file_path}, URL: {oss_url[:50]}...")
                return oss_url
            finally:
                # 清理临时文件
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)
        except ImportError:
            logger.warning(f"viapi.fileutils 未安装，使用普通 OSS 上传（OSS region: {settings.oss_region}, viapi region: {settings.viapi_region}），可能遇到地域不匹配问题")
            return self.upload_file(file_content, file_path, content_type)
        except Exception as e:
            logger.warning(f"使用 FileUtils 上传失败: {e}，降级到普通 OSS 上传（OSS region: {settings.oss_region}, viapi region: {settings.viapi_region}）")
            return self.upload_file(file_content, file_path, content_type)
    
    def generate_thumbnail(
        self,
        image_content: bytes,
        max_size: Tuple[int, int] = (300, 300)
    ) -> bytes:
        """
        Generate thumbnail from image
        """
        try:
            img = Image.open(io.BytesIO(image_content))
            # 转换为 RGB 模式（去除透明度）
            if img.mode in ('RGBA', 'LA', 'P'):
                # 创建白色背景
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')
            
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            output = io.BytesIO()
            img.save(output, format="JPEG", quality=85)
            return output.getvalue()
        except Exception as e:
            logger.warning(f"Thumbnail generation error: {e}, returning original image")
            return image_content
    
    def get_signed_url(self, file_path: str, expires: int = 3600) -> str:
        """
        Get signed URL for private file access
        """
        if self.mock_mode:
            # In mock mode, return full URL with base URL prefix
            if settings.static_domain:
                return f"https://{settings.static_domain.rstrip('/')}/{settings.oss_local_storage_path}/{file_path}"
            else:
                return f"{settings.base_url.rstrip('/')}/{settings.oss_local_storage_path}/{file_path}"
        
        try:
            url = self.bucket.sign_url('GET', file_path, expires)
            return url
        except Exception as e:
            logger.error(f"OSS signed URL error: {e}", exc_info=True)
            return f"https://cdn.lumina.ai/{file_path}"


storage_service = StorageService()

