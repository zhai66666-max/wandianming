"""从 GitHub 同步文件中恢复签到记录"""
import json
import os
from datetime import date, datetime
from app.models import Checkin


DATA_FILE = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), 'data', 'checkins.json'
)


def restore_checkins(db):
    """读取 data/checkins.json 恢复签到记录"""
    if not os.path.exists(DATA_FILE):
        return 0

    try:
        with open(DATA_FILE, 'r') as f:
            raw = f.read().strip()
            if not raw:
                return 0
            records = json.loads(raw)
    except (json.JSONDecodeError, IOError):
        return 0

    if not records:
        return 0

    restored = 0
    for r in records:
        try:
            person_id = int(r['person_id'])
            check_date = date.fromisoformat(r['check_date'])
            # 跳过已存在的记录
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
            c = Checkin(person_id=person_id, check_date=check_date, checked_at=checked_at)
            db.session.add(c)
            restored += 1
        except (KeyError, ValueError):
            continue

    if restored > 0:
        db.session.commit()
    return restored
