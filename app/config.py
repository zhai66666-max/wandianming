import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')

    # 数据库：优先使用 DATABASE_URL（如 Render PostgreSQL），否则用 SQLite
    _db_url = os.environ.get('DATABASE_URL', '')
    if _db_url:
        # Render 提供的 PostgreSQL URL 以 postgres:// 开头，SQLAlchemy 需要 postgresql://
        if _db_url.startswith('postgres://'):
            _db_url = _db_url.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = _db_url
    else:
        SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'instance', 'rollcall.db'
        )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # QQ 邮箱
    QQ_SENDER_EMAIL = os.environ.get('QQ_SENDER_EMAIL', '')
    QQ_AUTH_CODE = os.environ.get('QQ_AUTH_CODE', '')
    QQ_SMTP_SERVER = os.environ.get('QQ_SMTP_SERVER', 'smtp.qq.com')
    QQ_SMTP_PORT = int(os.environ.get('QQ_SMTP_PORT', '465'))

    # 管理员
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', '')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin123')

    # API 安全
    MONITOR_API_KEY = os.environ.get('MONITOR_API_KEY', '')

    # 监控
    MONITOR_WINDOW_DAYS = int(os.environ.get('MONITOR_WINDOW_DAYS', '3'))
