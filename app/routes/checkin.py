from flask import Blueprint, render_template, request, jsonify, current_app
from app import db
from app.models import Person, Checkin
from app.beijing_time import beijing_today

checkin_bp = Blueprint('checkin', __name__)


@checkin_bp.route('/')
def index():
    """签到页面"""
    persons = Person.query.filter_by(is_active=True).order_by(Person.name).all()
    today = beijing_today().isoformat()
    return render_template('checkin.html', persons=persons, today=today)


@checkin_bp.route('/api/persons')
def get_persons():
    """获取人员列表（JSON，用于搜索）"""
    persons = Person.query.filter_by(is_active=True).order_by(Person.name).all()
    return jsonify([p.to_dict() for p in persons])


@checkin_bp.route('/api/checkin', methods=['POST'])
def do_checkin():
    """执行签到"""
    data = request.get_json()
    person_id = data.get('person_id')

    if not person_id:
        return jsonify({'success': False, 'message': '请选择签到人员'}), 400

    person = Person.query.get(person_id)
    if not person or not person.is_active:
        return jsonify({'success': False, 'message': '人员不存在或已停用'}), 400

    # 检查今天是否已签到
    today = beijing_today()
    existing = Checkin.query.filter_by(person_id=person_id, check_date=today).first()
    if existing:
        return jsonify({
            'success': False,
            'message': f'{person.name} 今天已经签到过了（{existing.checked_at.strftime("%H:%M:%S")}）'
        }), 409

    # 创建签到记录
    checkin = Checkin(person_id=person_id, check_date=today)
    db.session.add(checkin)
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'{person.name} 签到成功！',
        'data': {
            'name': person.name,
            'time': checkin.checked_at.strftime('%H:%M:%S'),
            'date': today.isoformat(),
        }
    })


@checkin_bp.route('/api/checkins/today')
def today_checkins():
    """获取签到记录（默认今天，支持 ?date=YYYY-MM-DD）"""
    date_str = request.args.get('date', '')
    if date_str:
        try:
            from datetime import datetime
            target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            target_date = beijing_today()
    else:
        target_date = beijing_today()
    records = Checkin.query.filter_by(check_date=target_date).order_by(Checkin.checked_at.desc()).all()
    return jsonify([{
        'person_id': r.person_id,
        'name': r.person.name,
        'student_id': r.person.student_id,
        'time': r.checked_at.strftime('%H:%M:%S') if r.checked_at else '',
    } for r in records])


@checkin_bp.route('/api/checkins/export')
def export_checkins():
    """导出签到数据为 JSON（供 GitHub Actions 生成 Excel）"""
    from flask import current_app
    api_key = request.args.get('key', '')
    if api_key != current_app.config['MONITOR_API_KEY']:
        return jsonify({'error': 'unauthorized'}), 401

    target_date = request.args.get('date', beijing_today().isoformat())
    records = Checkin.query.filter_by(check_date=target_date).order_by(Checkin.checked_at.asc()).all()
    all_persons = Person.query.filter_by(is_active=True).order_by(Person.name).all()

    checked_dict = {r.person_id: r for r in records}

    result = []
    for p in all_persons:
        r = checked_dict.get(p.id)
        result.append({
            'name': p.name,
            'student_id': p.student_id,
            'department': p.department,
            'checked_in': r is not None,
            'time': r.checked_at.strftime('%H:%M:%S') if r and r.checked_at else '',
        })

    return jsonify({
        'date': target_date,
        'total': len(all_persons),
        'checked': len(records),
        'unchecked': len(all_persons) - len(records),
        'records': result,
    })


@checkin_bp.route('/api/checkins/all')
def all_checkins():
    """导出全部签到记录（备份用）"""
    from flask import current_app
    api_key = request.args.get('key', '')
    if api_key != current_app.config['MONITOR_API_KEY']:
        return jsonify({'error': 'unauthorized'}), 401

    records = Checkin.query.order_by(Checkin.check_date.desc(), Checkin.checked_at.desc()).all()
    return jsonify([{
        'person_id': r.person_id,
        'check_date': r.check_date.isoformat(),
        'checked_at': r.checked_at.isoformat() if r.checked_at else '',
    } for r in records])


@checkin_bp.route('/api/status')
def checkin_status():
    """查询今日签到状态"""
    person_id = request.args.get('person_id')
    if not person_id:
        return jsonify({'success': False, 'message': '缺少 person_id'}), 400

    today = beijing_today()
    checkin = Checkin.query.filter_by(person_id=person_id, check_date=today).first()

    if checkin:
        return jsonify({
            'success': True,
            'checked_in': True,
            'name': checkin.person.name,
            'time': checkin.checked_at.strftime('%H:%M:%S'),
        })
    return jsonify({'success': True, 'checked_in': False})
