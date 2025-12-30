from flask import Flask
from .config import Config
from .extensions import init_extensions

def create_app():
    app = Flask(__name__)
    app.secret_key = Config.FLASK_SECRET_KEY
    app.config.update(
        SESSION_COOKIE_SECURE=Config.SESSION_COOKIE_SECURE,
        SESSION_COOKIE_HTTPONLY=Config.SESSION_COOKIE_HTTPONLY,
        SESSION_COOKIE_SAMESITE=Config.SESSION_COOKIE_SAMESITE,
    )
    app.config['SERVER_NAME'] = Config.SERVER_NAME
    app.config['PREFERRED_URL_SCHEME'] = 'https' if Config.BACKEND_TLS else 'http'
    # Инициализация внешних сервисов (база данных, Redis, S3)
    init_extensions(app)

    # Регистрация маршрутов
    from .routes import register_routes
    register_routes(app)

    return app