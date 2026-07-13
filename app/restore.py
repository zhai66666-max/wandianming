"""从备份文件恢复签到记录"""
import json
import os
from datetime import date, datetime
from app.models import Checkin


def restore_checkins(db):
    """读取 data/backup.json 恢复签到记录"""
    backup_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 'data', 'backup.json'
    )

    if not os.path.exists(backup_path):
        return 0

    try:
        with open(backup_path, 'r') as f:
            records = json.load(f)
    except (json.JSONDecodeError, IOError):
        return 0

    restored = 0
    for r in records:
        try:
            check_date = date.fromisoformat(r['check_date'])
            person_id = r['person_id']
            # 检查是否已存在（避免重复）
            existing = Checkin.query.filter_by(
                person_id=person_id, check_date=check_date
            ).first()
            if not existing:
                checked_at = datetime.fromisoformat(r['checked_at']) if r.get('checked_at') else None
                c = Checkin(person_id=person_id, check_date=check_date, checked_at=checked_at)
                db.session.add(c)
                restored += 1
        except (KeyError, ValueError):
            continue

    if restored:
        db.session.commit()
    return restored
