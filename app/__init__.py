from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from app.config import Config

db = SQLAlchemy()


def create_app():
    import os

    app = Flask(__name__)
    app.config.from_object(Config)

    # 确保 instance 目录存在
    db_path = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_path.startswith('sqlite:///'):
        db_file_path = db_path.replace('sqlite:///', '')
        instance_dir = os.path.dirname(db_file_path)
        if instance_dir:
            os.makedirs(instance_dir, exist_ok=True)

    db.init_app(app)

    # 注册路由
    from app.routes.checkin import checkin_bp
    from app.routes.admin import admin_bp
    from app.routes.api import api_bp
    app.register_blueprint(checkin_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # 创建数据库表
    with app.app_context():
        db.create_all()

    # 配置 SQLite WAL 模式以支持并发写入
    from sqlalchemy import text
    with app.app_context():
        db.session.execute(text('PRAGMA journal_mode=WAL'))

    return app
