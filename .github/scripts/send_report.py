"""
从 GitHub Actions 调用监控 API，如果有缺勤人员则发送邮件。

环境变量（通过 GitHub Secrets 传入）:
    APP_URL - Render 部署的 URL
    MONITOR_API_KEY - API 密钥
    QQ_SENDER_EMAIL - QQ 邮箱地址
    QQ_AUTH_CODE - QQ 邮箱授权码
    ADMIN_EMAIL - 接收报告的邮箱
"""
import os
import sys
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from urllib.request import Request, urlopen
from urllib.error import URLError


def main():
    app_url = os.environ.get('APP_URL', '').rstrip('/')
    api_key = os.environ.get('MONITOR_API_KEY', '')

    if not app_url or not api_key:
        print('❌ APP_URL 或 MONITOR_API_KEY 未设置')
        sys.exit(1)

    # 调用监控 API
    print(f'📡 调用监控 API: {app_url}/api/monitor')
    req = Request(
        f'{app_url}/api/monitor',
        data=b'',
        headers={
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
        },
        method='POST',
    )

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except URLError as e:
        print(f'❌ API 调用失败: {e}')
        sys.exit(1)

    total = data['total_active']
    checked = data['checked_in']
    absent = data['absent']
    absent_list = data['absent_list']
    start = data['window_start']
    end = data['window_end']

    print(f'📊 活跃: {total}, 签到: {checked}, 缺勤: {absent}')

    if absent == 0:
        print('✅ 全部签到，无需发送邮件')
        return

    # 发送邮件
    smtp_server = 'smtp.qq.com'
    smtp_port = 465
    sender = os.environ.get('QQ_SENDER_EMAIL', '')
    auth_code = os.environ.get('QQ_AUTH_CODE', '')
    receiver = os.environ.get('ADMIN_EMAIL', '')

    if not all([sender, auth_code, receiver]):
        print('❌ QQ 邮箱配置不完整')
        sys.exit(1)

    # 构建邮件
    rows = ''
    for p in absent_list:
        sid = p.get('student_id', '-') or '-'
        rows += f'<tr><td>{p["name"]}</td><td>{sid}</td><td>{p.get("department", "-")}</td></tr>'

    total_days = (__import__('datetime').date.today() - __import__('datetime').date.fromisoformat(start)).days + 1

    html = f"""
    <html>
    <body style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
        <h2 style="color:#333;">📋 晚点名缺勤报告</h2>
        <p>监测周期: <strong>{start}</strong> 至 <strong>{end}</strong>（共 {total_days} 天）</p>
        <p style="color:#d32f2f;">在此期间以下 <strong>{absent} 人</strong>未完成任何一次签到：</p>
        <table border="1" cellpadding="10" cellspacing="0"
               style="border-collapse:collapse; width:100%; max-width:500px;">
            <tr style="background:#f5f5f5;">
                <th style="text-align:left;">姓名</th>
                <th style="text-align:left;">学号</th>
                <th style="text-align:left;">学院</th>
            </tr>
            {rows}
        </table>
        <p style="color:#999; font-size:12px; margin-top:30px;">此邮件由晚点名签到系统自动发送</p>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'[晚点名] 缺勤报告 - {start}至{end} - {absent}人未签到'
    msg['From'] = sender
    msg['To'] = receiver
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as server:
            server.login(sender, auth_code)
            server.sendmail(sender, [receiver], msg.as_string())
        print(f'📧 邮件发送成功: {absent} 人缺勤报告 → {receiver}')
    except Exception as e:
        print(f'❌ 邮件发送失败: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()
