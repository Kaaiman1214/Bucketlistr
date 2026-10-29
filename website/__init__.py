from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager

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

    from .models import User, BucketItem

    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(id):
        return User.query.get(int(id))

    return app

def create_database(app):
    # create_all only creates tables that are missing, so it is safe to run
    # on every start and will add the new bucket_item table to an old database.
    with app.app_context():
        db.create_all()
