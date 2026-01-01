"""
URL 辅助工具函数
用于生成正确的 API 和静态资源 URL
"""
from app.config import settings
from typing import Optional


def get_api_base_url() -> str:
    """
    获取 API 基础 URL
    
    Returns:
        API 基础 URL，例如：https://api.lumina.ai 或 http://localhost:8000
    """
    if settings.api_domain:
        return f"https://{settings.api_domain.rstrip('/')}"
    return settings.base_url.rstrip('/')


def get_static_base_url() -> str:
    """
    获取静态资源基础 URL
    
    Returns:
        静态资源基础 URL，例如：https://static.lumina.ai 或 http://localhost:8000
    """
    if settings.static_domain:
        return f"https://{settings.static_domain.rstrip('/')}"
    return settings.base_url.rstrip('/')


def get_api_url(path: str = "") -> str:
    """
    获取完整的 API URL
    
    Args:
        path: API 路径，例如：/v1/user/profile
        
    Returns:
        完整的 API URL
    """
    base_url = get_api_base_url()
    path = path.lstrip('/')
    return f"{base_url}/{path}" if path else base_url


def get_static_url(path: str = "") -> str:
    """
    获取完整的静态资源 URL
    
    Args:
        path: 静态资源路径，例如：uploads/image.jpg
        
    Returns:
        完整的静态资源 URL
    """
    base_url = get_static_base_url()
    path = path.lstrip('/')
    return f"{base_url}/{path}" if path else base_url

