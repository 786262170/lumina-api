import oss2
from typing import Optional, Tuple
from PIL import Image
import io
import os
from pathlib import Path
from app.config import settings
from app.utils.logger import logger


class StorageService:
    def __init__(self):
        self.mock_mode = settings.oss_mock_mode or not (settings.oss_access_key_id and settings.oss_access_key_secret)
        
        if not self.mock_mode:
            auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
            self.bucket = oss2.Bucket(auth, settings.oss_endpoint, settings.oss_bucket_name)
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
        
        # Real OSS mode
        try:
            self.bucket.put_object(file_path, file_content, headers={"Content-Type": content_type})
            # Use static_domain if configured, otherwise use OSS default URL
            if settings.static_domain:
                url = f"https://{settings.static_domain.rstrip('/')}/{file_path}"
            else:
                url = f"https://{settings.oss_bucket_name}.{settings.oss_endpoint}/{file_path}"
            logger.debug(f"File uploaded to OSS: {file_path}")
            return url
        except Exception as e:
            logger.error(f"OSS upload error: {e}", exc_info=True)
            raise
    
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

