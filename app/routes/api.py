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
