#!/bin/bash
# Lumina 域名配置脚本
# 用于快速配置 API 和静态资源域名

echo "=========================================="
echo "Lumina 域名配置助手"
echo "=========================================="
echo ""

# 检查 .env 文件是否存在
if [ ! -f .env ]; then
    echo "❌ 错误: .env 文件不存在"
    echo "请先创建 .env 文件"
    exit 1
fi

# 读取当前配置
echo "📋 当前域名配置："
grep -E "^API_DOMAIN=|^STATIC_DOMAIN=|^BASE_URL=" .env || echo "未找到域名配置"
echo ""

# 提示用户输入
read -p "请输入 API 域名 (例如: api.lumina.ai，留空跳过): " api_domain
read -p "请输入静态资源域名 (例如: static.lumina.ai，留空跳过): " static_domain

# 更新 .env 文件
if [ ! -z "$api_domain" ]; then
    # 移除协议前缀（如果有）
    api_domain=$(echo "$api_domain" | sed 's|https\?://||' | sed 's|/$||')
    
    # 更新或添加 API_DOMAIN
    if grep -q "^API_DOMAIN=" .env; then
        sed -i.bak "s|^API_DOMAIN=.*|API_DOMAIN=$api_domain|" .env
    else
        echo "" >> .env
        echo "# Domain Configuration" >> .env
        echo "API_DOMAIN=$api_domain" >> .env
    fi
    echo "✅ API 域名已更新: $api_domain"
fi

if [ ! -z "$static_domain" ]; then
    # 移除协议前缀（如果有）
    static_domain=$(echo "$static_domain" | sed 's|https\?://||' | sed 's|/$||')
    
    # 更新或添加 STATIC_DOMAIN
    if grep -q "^STATIC_DOMAIN=" .env; then
        sed -i.bak "s|^STATIC_DOMAIN=.*|STATIC_DOMAIN=$static_domain|" .env
    else
        if ! grep -q "^STATIC_DOMAIN=" .env; then
            echo "STATIC_DOMAIN=$static_domain" >> .env
        fi
    fi
    echo "✅ 静态资源域名已更新: $static_domain"
fi

# 更新 BASE_URL（如果设置了 API_DOMAIN）
if [ ! -z "$api_domain" ]; then
    if grep -q "^BASE_URL=" .env; then
        sed -i.bak "s|^BASE_URL=.*|BASE_URL=https://$api_domain|" .env
    else
        echo "BASE_URL=https://$api_domain" >> .env
    fi
    echo "✅ BASE_URL 已更新: https://$api_domain"
fi

# 清理备份文件
rm -f .env.bak

echo ""
echo "=========================================="
echo "✅ 域名配置完成！"
echo "=========================================="
echo ""
echo "📝 请确保："
echo "1. DNS 记录已正确配置"
echo "2. SSL 证书已申请并配置"
echo "3. Nginx 反向代理已配置（如需要）"
echo "4. 重启应用以加载新配置"
echo ""
echo "详细配置说明请参考: docs/域名配置指南.md"

