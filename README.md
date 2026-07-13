# 晚点名签到系统

一个轻量级的晚点名签到 Web 应用，适用于 100+ 人的日常签到管理。

## 功能

- 📱 **移动端签到**：每个人打开链接 → 搜索自己的名字 → 点击签到（适配微信内置浏览器）
- 📊 **管理后台**：查看签到统计、导入名单、管理成员
- 📧 **自动报告**：如果有人 5 天内未签到，自动通过 QQ 邮箱发送缺勤报告
- ⏰ **定时检查**：每天 22:00 自动运行（通过 GitHub Actions 触发）
- 💾 **SQLite 存储**：零配置，数据存为单个文件

## 快速开始（本地测试）

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd roll-call-system

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env，填入你的 QQ 邮箱等信息

# 5. 运行
python run.py
# 访问 http://localhost:5000
```

## 部署

### 方案一：Render（免费）

1. 将代码推送到 GitHub
2. 注册 [render.com](https://render.com)，用 GitHub 登录
3. 点击 "New Web Service"，选择你的仓库
4. Render 会自动读取 `render.yaml` 配置
5. 在 Render 环境变量中设置：
   - `QQ_SENDER_EMAIL`：发送报告的 QQ 邮箱
   - `QQ_AUTH_CODE`：QQ 邮箱授权码
   - `ADMIN_EMAIL`：接收报告的邮箱
   - `ADMIN_PASSWORD`：管理后台密码
6. 部署完成后，在 GitHub 的 Settings → Secrets 中添加：
   - `APP_URL`：Render 分配的 URL（如 `https://roll-call-system.onrender.com`）
   - `MONITOR_API_KEY`：与 Render 环境变量中相同的值

> **防止休眠**：Render 免费层 15 分钟无访问会休眠。取消 `.github/workflows/monitor.yml` 中 ping job 的注释（`if: false` 改为 `if: true`），GitHub Actions 会每 10 分钟 ping 一次保持活跃。

### 方案二：腾讯云轻量服务器（推荐，国内稳定）

```bash
# 1. SSH 登录服务器
ssh root@your-server-ip

# 2. 安装 Python 和 Nginx
apt update && apt install -y python3 python3-venv python3-pip nginx git

# 3. 克隆代码
cd /opt
git clone <your-repo-url> roll-call-system
cd roll-call-system

# 4. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 5. 配置 .env
cp .env.example .env
nano .env  # 填入真实配置

# 6. 创建数据库目录
mkdir -p instance
chmod 777 instance

# 7. 配置 systemd 服务
cp deploy/rollcall.service /etc/systemd/system/
# 编辑 /etc/systemd/system/rollcall.service，确保路径正确
systemctl daemon-reload
systemctl enable rollcall
systemctl start rollcall

# 8. 配置 Nginx
cp deploy/nginx.conf /etc/nginx/sites-available/rollcall
# 修改 server_name 为你的域名或 IP
ln -s /etc/nginx/sites-available/rollcall /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

# 9. 配置 SSL（如果有域名）
apt install -y certbot python3-certbot-nginx
certbot --nginx -d your-domain.com
```

### 方案三：自己电脑 + ngrok（临时使用）

```bash
# 1. 本地启动
python run.py

# 2. 另一个终端，用 ngrok 暴露到公网
ngrok http 5000
# 把 ngrok 生成的 URL 填入 GitHub Secrets 的 APP_URL
```

## QQ 邮箱配置

QQ 邮箱需要使用**授权码**而非 QQ 密码：

1. 登录 [QQ 邮箱](https://mail.qq.com)
2. 设置 → 账户 → POP3/IMAP/SMTP 服务
3. 开启 SMTP 服务，按提示发送短信验证
4. 获取 **16 位授权码**
5. 填入 `.env` 的 `QQ_AUTH_CODE`

> QQ 邮箱每天发送上限约 500 封。本系统每天最多发送 1 封汇总邮件，完全够用。

## 使用说明

### 管理员操作

1. 打开 `https://你的域名/admin`，输入管理密码
2. 在"导入名单"处粘贴名单（格式：`姓名,部门` 每行一个，部门可选）
3. 分享签到链接 `https://你的域名/` 到微信群/QQ群
4. 每天 22:00 会收到缺勤报告邮件

### 签到操作

1. 打开签到链接（手机/电脑均可）
2. 搜索自己的名字
3. 点击名字 → 点击"确认签到"
4. 看到 ✅ 签到成功即完成

## 名单格式

```
姓名,部门
张三,计算机学院
李四,数学学院
王五
```

- 每行一个人
- 逗号前是姓名（必填），逗号后是部门（可选）
- 同名人员会自动跳过，不会重复导入

## GitHub Secrets

在 GitHub 仓库 Settings → Secrets and variables → Actions 中添加：

| Secret | 说明 |
|--------|------|
| `APP_URL` | 部署后应用的 URL，如 `https://rollcall.example.com` |
| `MONITOR_API_KEY` | 与服务器 `.env` 中相同的 API 密钥 |

## 自定义设置

在 `.env` 中可以修改：

```bash
MONITOR_WINDOW_DAYS=5   # 监控窗口天数，默认 5 天
ADMIN_PASSWORD=admin123  # 管理后台密码
```

## 常见问题

**Q: 签到页面打不开？**
检查服务器是否在运行：`systemctl status rollcall`

**Q: 收不到邮件？**
1. 检查 `.env` 中 QQ 邮箱和授权码是否正确
2. 查看服务器日志：`journalctl -u rollcall -f`
3. 手动触发测试：`curl -X POST "http://localhost:5000/api/monitor" -H "Authorization: Bearer <MONITOR_API_KEY>"`

**Q: 如何添加/删除人员？**
管理后台可以导入新名单、停用/启用人员。停用的人员不会显示在签到列表中。

**Q: 数据库在哪里？**
SQLite 数据库在 `instance/rollcall.db`。备份只需复制这个文件。

## 项目结构

```
roll-call-system/
├── .github/workflows/monitor.yml   # GitHub Actions 定时触发
├── app/
│   ├── models.py                   # 数据库模型
│   ├── routes/
│   │   ├── checkin.py              # 签到路由
│   │   ├── admin.py                # 管理后台路由
│   │   └── api.py                  # API 端点
│   ├── services/
│   │   ├── monitor.py              # 缺勤检测逻辑
│   │   └── email_sender.py         # QQ 邮件发送
│   ├── templates/
│   │   ├── checkin.html            # 签到页面（移动端优先）
│   │   ├── admin.html              # 管理后台
│   │   └── admin_login.html        # 管理登录页
│   └── static/style.css            # 样式
├── data/roster.csv                 # 示例名单
├── deploy/                         # 部署配置文件
├── run.py                          # 启动入口
└── requirements.txt
```
