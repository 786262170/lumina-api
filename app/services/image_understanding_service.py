"""
Image understanding service using LiteLLM (unified SDK for multiple LLM providers)
Supports: OpenAI, GLM, Azure OpenAI, Anthropic, Google, etc.
"""
import httpx
import base64
import json
import re
from typing import Optional, Dict, Any, List
from app.config import settings
from app.utils.logger import logger


def _get_mock_result() -> Dict[str, Any]:
    """Get mock analysis result"""
    return {
        "description": "这是一张高质量的产品图片，展示了产品的细节和特点。",
        "tags": ["产品", "商业", "高质量"],
        "main_subject": "产品主体",
        "style": "专业摄影",
        "quality_score": 0.95,
        "suggestions": [
            "建议优化背景以突出主体",
            "可以调整光线以增强视觉效果"
        ]
    }


def _parse_json_response(content: str) -> Dict[str, Any]:
    """Parse JSON from response content, handling markdown code blocks"""
    try:
        # Try to extract JSON from markdown code blocks if present
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        elif "```" in content:
            json_start = content.find("```") + 3
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        
        return json.loads(content)
    except (json.JSONDecodeError, ValueError):
        # If not JSON, return as description
        return {
            "description": content,
            "tags": [],
            "main_subject": "未知",
            "style": "未知",
            "quality_score": 0.8,
            "suggestions": []
        }


async def _download_image_as_base64(image_url: str) -> Optional[str]:
    """Download image and convert to base64"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(image_url)
            if response.status_code != 200:
                logger.error(f"Failed to download image from {image_url}: {response.status_code}")
                return None
            image_base64 = base64.b64encode(response.content).decode('utf-8')
            return image_base64
    except Exception as e:
        logger.error(f"Error downloading image: {e}", exc_info=True)
        return None


def _get_model_name() -> str:
    """
    Get full model name with provider prefix
    Format: "provider/model-name" or just "model-name"
    """
    provider = settings.llm_provider.lower()
    model = settings.llm_model
    
    # If model already includes provider, use as is
    if "/" in model:
        return model
    
    # Map provider names to LiteLLM format
    provider_map = {
        "openai": "openai",
        "glm": "zhipuai",  # GLM uses zhipuai in LiteLLM
        "azure": "azure",
        "anthropic": "anthropic",
        "claude": "anthropic",
        "google": "gemini",
        "gemini": "gemini",
        "aliyun": "dashscope",  # 阿里云通义千问使用 dashscope
        "dashscope": "dashscope",  # 阿里云 DashScope
        "qwen": "dashscope",  # 通义千问别名
    }
    
    mapped_provider = provider_map.get(provider, provider)
    
    # Special handling for GLM
    if provider == "glm":
        # Use legacy config if available
        if settings.glm_api_key:
            return f"zhipuai/{model}"
        # Otherwise use standard format
        return f"zhipuai/{model}"
    
    return f"{mapped_provider}/{model}"


def _get_api_key() -> Optional[str]:
    """Get API key based on provider"""
    provider = settings.llm_provider.lower()
    
    # Use legacy GLM config if available
    if provider == "glm" and settings.glm_api_key:
        return settings.glm_api_key
    
    # Use unified API key
    if settings.llm_api_key:
        return settings.llm_api_key
    
    return None


async def analyze_image(
    image_url: str,
    prompt: Optional[str] = None,
    max_tokens: int = 1000
) -> Optional[Dict[str, Any]]:
    """
    Analyze image using LiteLLM (unified SDK for multiple LLM providers)
    
    Supported providers:
    - OpenAI: openai/gpt-4o, openai/gpt-4-vision-preview
    - GLM: zhipuai/glm-4v-plus
    - Azure OpenAI: azure/gpt-4o
    - Anthropic: anthropic/claude-3-opus-20240229
    - Google: gemini/gemini-pro-vision
    - 阿里云通义千问: dashscope/qwen-vl-plus, dashscope/qwen-vl-max, dashscope/qwen-vl
    
    Args:
        image_url: URL of the image to analyze
        prompt: Custom prompt for analysis
        max_tokens: Maximum tokens in response
    
    Returns:
        Analysis result dict or None if failed
    """
    if settings.llm_mock_mode or not _get_api_key():
        logger.debug("LLM mock mode: returning mock image analysis")
        return _get_mock_result()
    
    try:
        from litellm import acompletion
        
        # Download image
        image_base64 = await _download_image_as_base64(image_url)
        if not image_base64:
            return None
        
        # Default prompt
        if not prompt:
            prompt = """请详细分析这张图片，包括：
1. 图片的主要内容描述
2. 图片的风格和特点
3. 图片的质量评估
4. 改进建议（如果有）

请严格按照以下JSON格式返回：
{
  "description": "图片描述",
  "tags": ["标签1", "标签2"],
  "main_subject": "主要主体",
  "style": "风格",
  "quality_score": 0.95,
  "suggestions": ["建议1", "建议2"]
}"""
        
        # Get model name and API key
        model = _get_model_name()
        api_key = _get_api_key()
        
        # Prepare LiteLLM parameters
        litellm_params = {
            "model": model,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_base64}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ],
            "max_tokens": max_tokens,
            "temperature": 0.7,
        }
        
        # Add API key
        if api_key:
            # Set environment variable for LiteLLM
            import os
            provider = settings.llm_provider.lower()
            if provider == "glm" or "zhipuai" in model:
                os.environ["ZHIPUAI_API_KEY"] = api_key
            elif provider == "openai" or "openai" in model:
                os.environ["OPENAI_API_KEY"] = api_key
            elif provider == "azure":
                os.environ["AZURE_API_KEY"] = api_key
            elif provider == "anthropic" or "claude" in model:
                os.environ["ANTHROPIC_API_KEY"] = api_key
            elif provider == "google" or "gemini" in model:
                os.environ["GEMINI_API_KEY"] = api_key
            elif provider in ["aliyun", "dashscope", "qwen"] or "dashscope" in model or "qwen" in model.lower():
                os.environ["DASHSCOPE_API_KEY"] = api_key
            else:
                # Generic API key
                litellm_params["api_key"] = api_key
        
        # Add custom base URL if provided
        if settings.llm_base_url:
            litellm_params["api_base"] = settings.llm_base_url
        elif settings.llm_provider.lower() == "glm" and settings.glm_api_url:
            # Use legacy GLM URL
            litellm_params["api_base"] = settings.glm_api_url.replace("/chat/completions", "")
        
        # Call LiteLLM
        logger.debug(f"Calling LiteLLM with model: {model}, provider: {settings.llm_provider}")
        response = await acompletion(**litellm_params)
        
        # Extract content from response
        content = response.choices[0].message.content
        if not content:
            logger.warning("LiteLLM returned empty content")
            return None
        
        # Parse JSON response
        try:
            analysis_result = json.loads(content)
        except json.JSONDecodeError:
            # Fallback to text parsing
            analysis_result = _parse_json_response(content)
        
        logger.info(f"LiteLLM image analysis completed for {image_url} using {model}")
        return analysis_result
        
    except ImportError:
        logger.error("LiteLLM not installed. Please install: pip install litellm")
        return None
    except Exception as e:
        logger.error(f"LiteLLM image understanding error: {e}", exc_info=True)
        return None


async def get_image_tags(image_url: str) -> List[str]:
    """
    Get tags for an image
    
    Returns:
        List of tags
    """
    prompt = "请为这张图片生成5-10个标签，用JSON格式返回，格式：{\"tags\": [\"标签1\", \"标签2\", ...]}"
    result = await analyze_image(image_url, prompt, max_tokens=200)
    
    if result and "tags" in result:
        return result["tags"]
    elif result and "description" in result:
        # Fallback: extract keywords from description
        keywords = re.findall(r'[\u4e00-\u9fa5]+', result["description"])
        return keywords[:10] if keywords else []
    
    return []


async def get_image_description(image_url: str) -> str:
    """
    Get detailed description of an image
    
    Returns:
        Image description text
    """
    prompt = "请详细描述这张图片的内容、风格和特点。"
    result = await analyze_image(image_url, prompt, max_tokens=500)
    
    if result and "description" in result:
        return result["description"]
    
    return "无法生成图片描述"
