import os
from functools import wraps
from flask import Blueprint, request, jsonify, current_app

api_bp = Blueprint('api', __name__, url_prefix='/api')


def require_api_key(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get('Authorization', '')
        expected = f"Bearer {current_app.config['MONITOR_API_KEY']}"
        if not expected or auth != expected:
            return jsonify({'error': 'unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated


@api_bp.route('/monitor', methods=['POST'])
@require_api_key
def trigger_monitor():
    """触发缺勤检查并发送邮件（由 GitHub Actions 调用）"""
    from app.services.monitor import run_monitoring
    window_days = current_app.config.get('MONITOR_WINDOW_DAYS', 5)
    result = run_monitoring(window_days)
    return jsonify(result)


@api_bp.route('/ping', methods=['GET'])
def ping():
    """保活端点（防止 Render 休眠）"""
    return jsonify({'status': 'ok'})


@api_bp.route('/seed', methods=['POST'])
@require_api_key
def force_seed():
    """强制播种名单（需要 API Key）"""
    from app import db
    from app.seed import seed_if_empty
    # 先清空再播种
    from app.models import Person, Checkin
    Checkin.query.delete()
    Person.query.delete()
    db.session.commit()
    seeded = seed_if_empty(db)
    return jsonify({'success': True, 'seeded': seeded})


@api_bp.route('/debug', methods=['GET'])
def debug():
    """调试端点：查看数据库类型和状态"""
    from app import db
    from app.models import Person
    db_uri = current_app.config.get('SQLALCHEMY_DATABASE_URI', '')
    db_type = 'postgresql' if 'postgresql' in db_uri else 'sqlite'
    total = Person.query.count()
    return jsonify({
        'db_type': db_type,
        'db_uri_prefix': db_uri[:30] + '...' if len(db_uri) > 30 else db_uri,
        'total_persons': total,
    })
