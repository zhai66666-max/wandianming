"""北京时间工具函数。Render 服务器在美国，需要 +8 小时。"""
from datetime import datetime, date, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))


def beijing_now():
    """返回北京时间 datetime"""
    return datetime.now(BEIJING_TZ).replace(tzinfo=None)


def beijing_today():
    """返回北京时间 date"""
    return beijing_now().date()
