from datetime import date, timedelta
from app import db
from app.models import Person, Checkin


def run_monitoring(monitor_window_days=5):
    """
    检查最近 N 天内完全未签到的人员，并发送邮件报告。

    返回 dict:
        - total_active: 活跃人员总数
        - checked_in: 窗口内有签到的人数
        - absent: 完全未签到的人数
        - absent_list: 缺勤人员列表
        - window_start, window_end: 监控窗口
        - email_sent: 是否发送了邮件
    """
    today = date.today()
    start_date = today - timedelta(days=monitor_window_days)

    # 活跃人员
    all_active = Person.query.filter_by(is_active=True).all()
    all_ids = {p.id for p in all_active}

    # 窗口内有签到记录的人员 ID
    checked_result = db.session.query(Checkin.person_id).filter(
        Checkin.check_date >= start_date,
        Checkin.check_date <= today
    ).distinct().all()
    checked_ids = {r[0] for r in checked_result}

    # 完全未签到的人员
    absent_ids = all_ids - checked_ids
    absent_persons = [p for p in all_active if p.id in absent_ids]

    result = {
        'total_active': len(all_active),
        'checked_in': len(checked_ids),
        'absent': len(absent_persons),
        'absent_list': [
            {'name': p.name, 'student_id': getattr(p, 'student_id', ''), 'department': p.department}
            for p in absent_persons
        ],
        'window_start': start_date.isoformat(),
        'window_end': today.isoformat(),
        'email_sent': False,
    }

    # 如果存在缺勤人员，发送邮件
    if absent_persons:
        from app.services.email_sender import send_absence_report
        success = send_absence_report(absent_persons, start_date, today)
        result['email_sent'] = success

    return result
