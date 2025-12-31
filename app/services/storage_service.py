import oss2
from typing import Optional, Tuple
from PIL import Image
import io
from app.config import settings
from app.utils.logger import logger


class StorageService:
    def __init__(self):
        if settings.oss_access_key_id and settings.oss_access_key_secret:
            auth = oss2.Auth(settings.oss_access_key_id, settings.oss_access_key_secret)
            self.bucket = oss2.Bucket(auth, settings.oss_endpoint, settings.oss_bucket_name)
        else:
            self.bucket = None
    
    def upload_file(
        self,
        file_content: bytes,
        file_path: str,
        content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload file to OSS
        Returns: file URL
        """
        if not self.bucket:
            # Mock mode: return mock URL
            return f"https://cdn.lumina.ai/{file_path}"
        
        try:
            self.bucket.put_object(file_path, file_content, headers={"Content-Type": content_type})
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
        if not self.bucket:
            return f"https://cdn.lumina.ai/{file_path}"
        
        try:
            url = self.bucket.sign_url('GET', file_path, expires)
            return url
        except Exception as e:
            logger.error(f"OSS signed URL error: {e}", exc_info=True)
            return f"https://cdn.lumina.ai/{file_path}"


storage_service = StorageService()

