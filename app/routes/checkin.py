from flask import Blueprint, render_template, request, jsonify, current_app
from datetime import date
from app import db
from app.models import Person, Checkin

checkin_bp = Blueprint('checkin', __name__)


@checkin_bp.route('/')
def index():
    """签到页面"""
    persons = Person.query.filter_by(is_active=True).order_by(Person.name).all()
    today = date.today().isoformat()
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
    today = date.today()
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


@checkin_bp.route('/api/status')
def checkin_status():
    """查询今日签到状态"""
    person_id = request.args.get('person_id')
    if not person_id:
        return jsonify({'success': False, 'message': '缺少 person_id'}), 400

    today = date.today()
    checkin = Checkin.query.filter_by(person_id=person_id, check_date=today).first()

    if checkin:
        return jsonify({
            'success': True,
            'checked_in': True,
            'name': checkin.person.name,
            'time': checkin.checked_at.strftime('%H:%M:%S'),
        })
    return jsonify({'success': True, 'checked_in': False})
