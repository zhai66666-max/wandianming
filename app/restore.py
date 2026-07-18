"""启动时从 GitHub data 分支下载签到记录并恢复"""
import json
import os
from datetime import date, datetime
from urllib.request import urlopen
from urllib.error import URLError
from app.models import Checkin

# GitHub data 分支的 raw URL
BACKUP_URL = 'https://raw.githubusercontent.com/zhai66666-max/wandianming/data/data/checkins.json'
LOCAL_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'checkins.json'
)


def _load_records():
    """加载签到记录：优先本地文件，不存在则从 GitHub 下载"""
    # 1. 尝试本地
    if os.path.exists(LOCAL_FILE):
        try:
            with open(LOCAL_FILE, 'r') as f:
                raw = f.read().strip()
                if raw and raw != '[]':
                    return json.loads(raw)
        except (json.JSONDecodeError, IOError):
            pass

    # 2. 从 GitHub data 分支下载
    try:
        with urlopen(BACKUP_URL, timeout=10) as resp:
            raw = resp.read().decode('utf-8').strip()
            if raw and raw != '[]':
                return json.loads(raw)
    except (URLError, Exception):
        pass

    return []


def restore_checkins(db):
    """恢复签到记录"""
    records = _load_records()
    if not records:
        return 0

    restored = 0
    for r in records:
        try:
            person_id = int(r['person_id'])
            check_date = date.fromisoformat(r['check_date'])
            existing = Checkin.query.filter_by(
                person_id=person_id, check_date=check_date
            ).first()
            if existing:
                continue
            checked_at = None
            if r.get('checked_at'):
                try:
                    checked_at = datetime.fromisoformat(r['checked_at'])
                except (ValueError, TypeError):
                    pass
            db.session.add(Checkin(
                person_id=person_id, check_date=check_date, checked_at=checked_at
            ))
            restored += 1
        except (KeyError, ValueError):
            continue

    if restored > 0:
        db.session.commit()
    return restored
