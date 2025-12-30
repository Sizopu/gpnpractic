from flask import Flask
def register_routes(app: Flask):
    """Регистрирует все blueprint'ы маршрутов."""
    from . import main, auth, gallery, library
    app.register_blueprint(main.bp)
    app.register_blueprint(auth.bp)
    app.register_blueprint(gallery.bp)
    app.register_blueprint(library.bp)