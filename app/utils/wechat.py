import httpx
from typing import Optional, Dict, Any
from app.config import settings


async def get_wechat_user_info(code: str) -> Optional[Dict[str, Any]]:
    """
    Get WeChat user info from authorization code
    Returns user info dict or None if failed
    """
    if settings.wechat_mock_mode:
        # Mock mode: return mock user info
        return {
            "openid": f"mock_openid_{code}",
            "nickname": "微信用户",
            "headimgurl": "https://cdn.lumina.ai/default_avatar.jpg",
            "unionid": f"mock_unionid_{code}" if hasattr(settings, 'wechat_unionid') else None
        }
    
    # Real WeChat OAuth flow
    if not settings.wechat_app_id or not settings.wechat_app_secret:
        return None
    
    try:
        # Step 1: Exchange code for access_token
        async with httpx.AsyncClient() as client:
            token_url = "https://api.weixin.qq.com/sns/oauth2/access_token"
            token_params = {
                "appid": settings.wechat_app_id,
                "secret": settings.wechat_app_secret,
                "code": code,
                "grant_type": "authorization_code"
            }
            token_response = await client.get(token_url, params=token_params)
            token_data = token_response.json()
            
            if "errcode" in token_data:
                return None
            
            access_token = token_data.get("access_token")
            openid = token_data.get("openid")
            
            # Step 2: Get user info
            user_info_url = "https://api.weixin.qq.com/sns/userinfo"
            user_params = {
                "access_token": access_token,
                "openid": openid,
                "lang": "zh_CN"
            }
            user_response = await client.get(user_info_url, params=user_params)
            user_data = user_response.json()
            
            if "errcode" in user_data:
                return None
            
            return {
                "openid": openid,
                "nickname": user_data.get("nickname", "微信用户"),
                "headimgurl": user_data.get("headimgurl", ""),
                "unionid": user_data.get("unionid")
            }
    except Exception as e:
        # Log error
        print(f"WeChat OAuth error: {e}")
        return None

