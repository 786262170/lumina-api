#!/usr/bin/env python3
"""
微信授权码获取工具

这个脚本帮助你生成微信授权 URL，用于获取 code。

注意：code 不能直接通过 API 获取，需要用户授权。
"""

import urllib.parse
from app.config import settings

def generate_wechat_auth_url(redirect_uri: str, scope: str = "snsapi_userinfo", state: str = None):
    """
    生成微信授权 URL
    
    Args:
        redirect_uri: 授权回调地址（需要与微信开放平台配置的一致）
        scope: 授权范围
            - snsapi_base: 静默授权，仅获取 openid
            - snsapi_userinfo: 需要用户确认，可获取用户信息
        state: 可选，用于防止 CSRF 攻击的随机字符串
    """
    app_id = settings.wechat_app_id
    
    if not app_id:
        print("❌ 错误：未配置 WECHAT_APP_ID")
        print("请在 .env 文件中设置 WECHAT_APP_ID")
        return None
    
    # 构建授权 URL
    params = {
        "appid": app_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": scope,
    }
    
    if state:
        params["state"] = state
    
    # 构建查询字符串
    query_string = urllib.parse.urlencode(params)
    auth_url = f"https://open.weixin.qq.com/connect/oauth2/authorize?{query_string}#wechat_redirect"
    
    return auth_url


def main():
    print("=" * 60)
    print("微信授权码 (code) 获取工具")
    print("=" * 60)
    print()
    
    # 检查配置
    if not settings.wechat_app_id:
        print("❌ 错误：未配置 WECHAT_APP_ID")
        print("请在 .env 文件中设置：")
        print("  WECHAT_APP_ID=wx68bd5e55d855bf4d")
        return
    
    if not settings.wechat_app_secret:
        print("⚠️  警告：未配置 WECHAT_APP_SECRET")
        print("请在 .env 文件中设置：")
        print("  WECHAT_APP_SECRET=your_secret")
        print()
    
    print(f"✅ AppID: {settings.wechat_app_id}")
    print()
    
    # 获取用户输入
    print("请选择授权范围：")
    print("  1. snsapi_base - 静默授权（仅获取 openid）")
    print("  2. snsapi_userinfo - 需要用户确认（可获取用户信息）")
    choice = input("请选择 (1/2，默认 2): ").strip() or "2"
    
    scope = "snsapi_base" if choice == "1" else "snsapi_userinfo"
    
    print()
    print("请输入授权回调地址（redirect_uri）：")
    print("  示例：https://yourdomain.com/auth/callback")
    print("  注意：必须与微信开放平台配置的授权回调域名匹配")
    redirect_uri = input("回调地址: ").strip()
    
    if not redirect_uri:
        print("❌ 错误：回调地址不能为空")
        return
    
    # 生成授权 URL
    auth_url = generate_wechat_auth_url(redirect_uri, scope)
    
    print()
    print("=" * 60)
    print("授权 URL 已生成")
    print("=" * 60)
    print()
    print("📋 授权 URL：")
    print(auth_url)
    print()
    print("=" * 60)
    print("使用说明")
    print("=" * 60)
    print()
    print("1. 复制上面的授权 URL")
    print("2. 在微信内置浏览器中打开（或使用微信扫码）")
    print("3. 用户同意授权后，微信会跳转到你的回调地址")
    print("4. 回调 URL 中会包含 code 参数，例如：")
    print(f"   {redirect_uri}?code=081abc123def456&state=xxx")
    print("5. 从 URL 中提取 code 参数")
    print()
    print("⚠️  重要提示：")
    print("  - code 有效期只有 5 分钟")
    print("  - code 只能使用一次")
    print("  - 获取 code 后立即发送到后端 API")
    print()
    print("测试 API 调用示例：")
    print("  curl -X POST http://localhost:8000/v1/auth/wechat-login \\")
    print("    -H 'Content-Type: application/json' \\")
    print("    -d '{\"code\": \"YOUR_CODE_HERE\"}'")
    print()


if __name__ == "__main__":
    main()

