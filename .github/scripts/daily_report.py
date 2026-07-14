"""
每日签到报告：凌晨 0:30 发送前一天的签到 Excel 报表。
"""
import os
import sys
import json
import smtplib
import tempfile
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from urllib.request import Request, urlopen
from urllib.error import URLError
from datetime import datetime, timedelta, timezone
import pandas as pd

BEIJING = timezone(timedelta(hours=8))


def beijing_today():
    return datetime.now(BEIJING).date()


def main():
    app_url = os.environ.get('APP_URL', '').rstrip('/')
    api_key = os.environ.get('MONITOR_API_KEY', '')

    if not app_url or not api_key:
        print('❌ APP_URL 或 MONITOR_API_KEY 未设置')
        sys.exit(1)

    # 凌晨 0:30 运行 → 查前一天
    yesterday = (beijing_today() - timedelta(days=1)).isoformat()

    print(f'📡 获取 {yesterday} 签到数据')
    url = f'{app_url}/api/checkins/export?key={api_key}&date={yesterday}'
    req = Request(url)

    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
    except URLError as e:
        print(f'❌ API 调用失败: {e}')
        sys.exit(1)

    total = data['total']
    checked = data['checked']
    unchecked = data['unchecked']
    records = data['records']
    rate = round(checked / total * 100, 1) if total > 0 else 0

    print(f'📊 总人数:{total} 已签到:{checked} 未签到:{unchecked} 签到率:{rate}%')

    # 生成 Excel
    df = pd.DataFrame(records)
    df.columns = ['姓名', '学号', '学院', '是否签到', '签到时间']
    df['是否签到'] = df['是否签到'].apply(lambda x: '✅ 已签到' if x else '❌ 未签到')

    tmpdir = tempfile.mkdtemp()
    xlsx_path = os.path.join(tmpdir, f'晚点名签到_{yesterday}.xlsx')

    with pd.ExcelWriter(xlsx_path, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='签到明细', index=False)
        df_checked = df[df['是否签到'] == '✅ 已签到']
        df_checked.to_excel(writer, sheet_name='已签到', index=False)
        df_unchecked = df[df['是否签到'] == '❌ 未签到']
        df_unchecked.to_excel(writer, sheet_name='未签到', index=False)

    # 发送邮件
    smtp_server = 'smtp.qq.com'
    smtp_port = 465
    sender = os.environ.get('QQ_SENDER_EMAIL', '')
    auth_code = os.environ.get('QQ_AUTH_CODE', '')
    admin_emails = os.environ.get('ADMIN_EMAIL', '')
    receivers = [e.strip() for e in admin_emails.split(',') if e.strip()]

    if not all([sender, auth_code]) or not receivers:
        print('❌ 邮箱配置不完整')
        sys.exit(1)

    html = f"""
    <html>
    <body style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
        <h2>📋 晚点名签到日报</h2>
        <p>日期: <strong>{yesterday}</strong></p>
        <table border="1" cellpadding="8" cellspacing="0"
               style="border-collapse:collapse; width:100%; max-width:400px;">
            <tr><td>总人数</td><td><strong>{total}</strong></td></tr>
            <tr><td style="color:#4caf50;">✅ 已签到</td><td><strong>{checked}</strong></td></tr>
            <tr><td style="color:#f44336;">❌ 未签到</td><td><strong>{unchecked}</strong></td></tr>
            <tr><td>签到率</td><td><strong>{rate}%</strong></td></tr>
        </table>
        <p>📎 详细名单见附件 Excel</p>
        <p style="color:#999; font-size:12px; margin-top:20px;">此邮件由晚点名签到系统自动发送</p>
    </body>
    </html>
    """

    msg = MIMEMultipart()
    msg['Subject'] = f'[晚点名] 签到日报 - {yesterday} - {checked}/{total} ({rate}%)'
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    msg.attach(MIMEText(html, 'html', 'utf-8'))

    with open(xlsx_path, 'rb') as f:
        part = MIMEBase('application', 'octet-stream')
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header('Content-Disposition',
                        f'attachment; filename="晚点名签到_{yesterday}.xlsx"')
        msg.attach(part)

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15) as server:
            server.login(sender, auth_code)
            server.sendmail(sender, receivers, msg.as_string())
        print(f'📧 日报发送成功 → {", ".join(receivers)}')
    except Exception as e:
        print(f'❌ 邮件发送失败: {e}')
        sys.exit(1)

    os.remove(xlsx_path)
    os.rmdir(tmpdir)


if __name__ == '__main__':
    main()
