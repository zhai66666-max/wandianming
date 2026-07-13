import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date


def send_absence_report(absent_persons, start_date: date, end_date: date):
    """
    发送缺勤报告邮件。

    Args:
        absent_persons: 缺勤的 Person 对象列表
        start_date: 监控开始日期
        end_date: 监控结束日期

    Returns:
        bool: 发送是否成功
    """
    smtp_server = os.environ.get('QQ_SMTP_SERVER', 'smtp.qq.com')
    smtp_port = int(os.environ.get('QQ_SMTP_PORT', '465'))
    sender_email = os.environ.get('QQ_SENDER_EMAIL', '')
    auth_code = os.environ.get('QQ_AUTH_CODE', '')
    admin_email = os.environ.get('ADMIN_EMAIL', '')

    if not all([sender_email, auth_code, admin_email]):
        print('[EMAIL] 邮件配置不完整，跳过发送')
        print(f'  SENDER: {sender_email}, AUTH_CODE: {"已设置" if auth_code else "未设置"}, ADMIN: {admin_email}')
        return False

    total_days = (end_date - start_date).days + 1
    absent_count = len(absent_persons)

    # 构建 HTML 表格
    rows = ''
    for p in absent_persons:
        sid = getattr(p, 'student_id', '') or '-'
        rows += f'<tr><td>{p.name}</td><td>{sid}</td><td>{p.department or "-"}</td></tr>'

    html_body = f"""
    <html>
    <body style="font-family: 'Microsoft YaHei', Arial, sans-serif;">
        <h2 style="color:#333;">📋 晚点名缺勤报告</h2>
        <p>监测周期: <strong>{start_date}</strong> 至 <strong>{end_date}</strong>（共 {total_days} 天）</p>
        <p style="color:#d32f2f;">在此期间以下 <strong>{absent_count} 人</strong>未完成任何一次签到：</p>
        <table border="1" cellpadding="10" cellspacing="0"
               style="border-collapse:collapse; width:100%; max-width:500px;">
            <tr style="background:#f5f5f5;">
                <th style="text-align:left;">姓名</th>
                <th style="text-align:left;">学号</th>
                <th style="text-align:left;">部门</th>
            </tr>
            {rows}
        </table>
        <p style="color:#999; font-size:12px; margin-top:30px;">
            此邮件由晚点名签到系统自动发送<br>
            发送时间: {date.today().isoformat()}
        </p>
    </body>
    </html>
    """

    msg = MIMEMultipart('alternative')
    msg['Subject'] = f'[晚点名] 缺勤报告 - {start_date}至{end_date} - {absent_count}人未签到'
    msg['From'] = sender_email
    msg['To'] = admin_email
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    try:
        with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
            server.login(sender_email, auth_code)
            server.sendmail(sender_email, [admin_email], msg.as_string())
        print(f'[EMAIL] 邮件发送成功: {absent_count} 人缺勤报告 → {admin_email}')
        return True
    except smtplib.SMTPAuthenticationError:
        print('[EMAIL] QQ 邮箱认证失败，请检查 QQ_SENDER_EMAIL 和 QQ_AUTH_CODE')
        return False
    except Exception as e:
        print(f'[EMAIL] 邮件发送失败: {e}')
        return False
