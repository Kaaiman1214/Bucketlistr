import os
import secrets
from os import path

from flask import Flask, jsonify
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import inspect, text

db = SQLAlchemy()
DB_NAME = "database.db"
DATA_DIR = path.abspath(os.environ.get('BUCKETLIST_DATA_DIR') or path.dirname(__file__))
DB_PATH = path.join(DATA_DIR, DB_NAME)
IMAGE_DIR = path.join(DATA_DIR, 'images')
PENDING_DIR = path.join(IMAGE_DIR, 'pending')
MAX_UPLOAD_MB = 250


def load_secret_key():
    secret_key = os.environ.get('SECRET_KEY')
    if secret_key:
        return secret_key

    key_path = path.join(DATA_DIR, 'secret_key')
    try:
        with open(key_path) as key_file:
            stored = key_file.read().strip()
        if stored:
            return stored
    except OSError:
        pass

    secret_key = secrets.token_hex(32)
    try:
        descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
        with os.fdopen(descriptor, 'w') as key_file:
            key_file.write(secret_key)
    except OSError:
        print('WARNING: SECRET_KEY is not set and could not be stored, using a temporary key.')
    return secret_key


def create_app():
    app = Flask(__name__)
    os.makedirs(PENDING_DIR, exist_ok=True)
    app.config['SECRET_KEY'] = load_secret_key()
    app.config['MAX_CONTENT_LENGTH'] = MAX_UPLOAD_MB * 1024 * 1024
    database_uri_path = DB_PATH.replace('\\', '/')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_uri_path}'
    db.init_app(app)

    from .security import init_security
    init_security(app)

    from .views import views
    from .auth import auth
    from .settings import settings

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')
    app.register_blueprint(settings, url_prefix='/')

    @app.errorhandler(413)
    def upload_too_large(error):
        return jsonify(error=f'That photo is too large. The limit is {MAX_UPLOAD_MB} MB.'), 413

    from .models import User, BucketItem, get_site_name, get_sidebar_categories

    create_database(app)

    from .images import backfill_derived_images, remove_stale_pending
    remove_stale_pending()
    backfill_derived_images(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to edit the bucketlist.'
    login_manager.login_message_category = 'error'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    @app.context_processor
    def inject_layout():
        return {'site_name': get_site_name(),
                'sidebar_categories': get_sidebar_categories()}

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
