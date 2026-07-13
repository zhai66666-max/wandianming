from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from datetime import date, timedelta
from app import db
from app.models import Person, Checkin

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def _check_auth():
    """简单的密码认证"""
    from flask import current_app, session
    password = request.form.get('password', '') or request.args.get('password', '')
    if password == current_app.config['ADMIN_PASSWORD']:
        session['admin_authenticated'] = True
        return True
    if session.get('admin_authenticated'):
        return True
    return False


@admin_bp.route('/', methods=['GET', 'POST'], strict_slashes=False)
@admin_bp.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    """管理后台"""
    if not _check_auth():
        return render_template('admin_login.html')

    today = date.today()

    # 统计
    total = Person.query.filter_by(is_active=True).count()
    today_checked = Checkin.query.filter_by(check_date=today).count()
    unchecked = total - today_checked
    rate = round(today_checked / total * 100, 1) if total > 0 else 0

    # 今日未签到人员
    from sqlalchemy import select
    checked_ids = select(Checkin.person_id).where(Checkin.check_date == today)
    unchecked_persons = Person.query.filter(
        Person.is_active == True,
        Person.id.notin_(checked_ids)
    ).order_by(Person.name).all()

    # 近 3 天连续未打卡人员
    from datetime import timedelta
    three_days_ago = today - timedelta(days=3)
    checked_3days = db.session.query(Checkin.person_id).filter(
        Checkin.check_date >= three_days_ago,
        Checkin.check_date <= today
    ).distinct().all()
    checked_3days_ids = {r[0] for r in checked_3days}
    absent_3days = Person.query.filter(
        Person.is_active == True,
        Person.id.notin_(checked_3days_ids) if checked_3days_ids else True
    ).order_by(Person.name).all()

    # 最近 7 天签到率
    daily_stats = []
    for i in range(6, -1, -1):
        d = today - timedelta(days=i)
        count = Checkin.query.filter_by(check_date=d).count()
        daily_stats.append({
            'date': d.isoformat(),
            'count': count,
            'rate': round(count / total * 100, 1) if total > 0 else 0,
        })

    return render_template(
        'admin.html',
        total=total,
        today_checked=today_checked,
        unchecked=unchecked,
        rate=rate,
        unchecked_persons=unchecked_persons,
        absent_3days=absent_3days,
        daily_stats=daily_stats,
        today=today,
    )


@admin_bp.route('/import', methods=['POST'])
def import_roster():
    """导入名单"""
    if not _check_auth():
        return jsonify({'success': False, 'message': '未授权'}), 401

    data = request.get_json()
    persons_data = data.get('persons', [])

    if not persons_data:
        return jsonify({'success': False, 'message': '名单为空'}), 400

    added = 0
    skipped = 0
    errors = []

    for item in persons_data:
        name = item.get('name', '').strip()
        if not name:
            errors.append(f'跳过空姓名: {item}')
            skipped += 1
            continue

        # 检查是否同名已存在
        existing = Person.query.filter_by(name=name).first()
        if existing:
            errors.append(f'{name} 已存在，跳过')
            skipped += 1
            continue

        person = Person(
            name=name,
            student_id=item.get('student_id', '').strip(),
            department=item.get('department', '').strip(),
        )
        db.session.add(person)
        added += 1

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'导入完成：新增 {added} 人，跳过 {skipped} 人',
        'added': added,
        'skipped': skipped,
        'errors': errors[:10],  # 最多显示 10 条错误
    })


@admin_bp.route('/persons', methods=['GET'])
def list_persons():
    """列出所有人员"""
    if not _check_auth():
        return jsonify({'success': False, 'message': '未授权'}), 401

    persons = Person.query.order_by(Person.name).all()
    return jsonify([p.to_dict() for p in persons])


@admin_bp.route('/persons/<int:person_id>/toggle', methods=['POST'])
def toggle_person(person_id):
    """启用/停用人员"""
    if not _check_auth():
        return jsonify({'success': False, 'message': '未授权'}), 401

    person = Person.query.get_or_404(person_id)
    person.is_active = not person.is_active
    db.session.commit()
    return jsonify({
        'success': True,
        'message': f'{person.name} 已{"启用" if person.is_active else "停用"}',
        'is_active': person.is_active,
    })


@admin_bp.route('/persons/<int:person_id>/delete', methods=['POST'])
def delete_person(person_id):
    """删除人员（同时删除其签到记录）"""
    if not _check_auth():
        return jsonify({'success': False, 'message': '未授权'}), 401

    person = Person.query.get_or_404(person_id)
    name = person.name

    # 删除签到记录
    Checkin.query.filter_by(person_id=person_id).delete()
    # 删除人员
    db.session.delete(person)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{name} 已删除',
    })


@admin_bp.route('/logout')
def logout():
    from flask import session
    session.pop('admin_authenticated', None)
    return redirect(url_for('admin.dashboard'))
