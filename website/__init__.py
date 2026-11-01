import os
import secrets
from os import path

from flask import Flask, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db = SQLAlchemy()
DB_NAME = "database.db"
DB_PATH = path.join(path.dirname(path.abspath(__file__)), DB_NAME)
IMAGE_DIR = path.join(path.dirname(path.abspath(__file__)), 'images')
PENDING_DIR = path.join(IMAGE_DIR, 'pending')
MAX_UPLOAD_MB = 30


def create_app():
    app = Flask(__name__)
    secret_key = os.environ.get('SECRET_KEY')
    if not secret_key:
        secret_key = secrets.token_hex(32)
        print('WARNING: SECRET_KEY is not set, using a temporary key.')
    app.config['SECRET_KEY'] = secret_key
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024
    os.makedirs(PENDING_DIR, exist_ok=True)
    database_uri_path = DB_PATH.replace('\\', '/')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_uri_path}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    @app.errorhandler(413)
    def upload_too_large(error):
        return jsonify(error=f'That photo is too large. The limit is {MAX_UPLOAD_MB} MB.'), 413

    from .models import User, BucketItem, get_site_name

    create_database(app)

    from .images import remove_stale_pending
    remove_stale_pending()

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to edit the bucketlist.'
    login_manager.login_message_category = 'error'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    @app.context_processor
    def inject_site_name():
        return {'site_name': get_site_name()}

    return app


def create_database(app):
    with app.app_context():
        db.create_all()
        add_missing_columns()


def add_missing_columns():
    inspector = inspect(db.engine)
    for table in db.metadata.sorted_tables:
        existing = {column['name'] for column in inspector.get_columns(table.name)}
        for column in table.columns:
            if column.name in existing:
                continue
            if not column.nullable:
                print(f'WARNING: cannot add NOT NULL column {table.name}.{column.name} '
                      'automatically; delete database.db or add it by hand.')
                continue
            column_type = column.type.compile(dialect=db.engine.dialect)
            db.session.execute(text(
                f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column_type}'))
            print(f'Added missing column {table.name}.{column.name}')
    db.session.commit()
