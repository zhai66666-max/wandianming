#!/bin/bash
# 晚点名签到系统 - 配置脚本
# 运行: bash setup.sh

set -e

echo "========================================"
echo "  晚点名签到系统 - 环境配置"
echo "========================================"
echo ""

# QQ 邮箱配置
read -p "QQ 邮箱地址（用于发送报告）: " QQ_EMAIL
read -sp "QQ 邮箱授权码（16位，输入时不显示）: " QQ_AUTH
echo ""
read -p "接收报告的邮箱: " ADMIN_EMAIL
echo ""

# 生成随机密钥
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(24))")
MONITOR_API_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))")

# 写入 .env
cat > .env << EOF
# Flask
SECRET_KEY=$SECRET_KEY

# QQ 邮箱配置
QQ_SENDER_EMAIL=$QQ_EMAIL
QQ_AUTH_CODE=$QQ_AUTH
QQ_SMTP_SERVER=smtp.qq.com
QQ_SMTP_PORT=465

# 管理员
ADMIN_EMAIL=$ADMIN_EMAIL
ADMIN_PASSWORD=admin123

# 监控 API 密钥
MONITOR_API_KEY=$MONITOR_API_KEY

# 监控窗口天数
MONITOR_WINDOW_DAYS=5
EOF

echo "✅ .env 配置完成！"
echo ""
echo "📋 配置摘要:"
echo "  发件邮箱: $QQ_EMAIL"
echo "  接收邮箱: $ADMIN_EMAIL"
echo "  管理密码: admin123"
echo ""
echo "⚠️  请记住 MONITOR_API_KEY（部署 Render 和 GitHub Secrets 需要）:"
echo "  $MONITOR_API_KEY"
echo ""
echo "下一步: 部署到 Render 或推送到 GitHub"
