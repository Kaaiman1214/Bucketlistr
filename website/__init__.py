from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path

db = SQLAlchemy()
DB_NAME = "database.db"
DB_PATH = path.join(path.dirname(path.abspath(__file__)), DB_NAME)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'kwhdkmBJSD&@ ^%hkasdhbchsba&#'
    database_uri_path = DB_PATH.replace('\\', '/')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{database_uri_path}'
    db.init_app(app)

    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, BLItem

    create_database(app)

    return app

def create_database(app):
    if not path.exists(DB_PATH):
        with app.app_context():
            db.create_all()
        print('Created Database!')
