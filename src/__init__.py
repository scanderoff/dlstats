from flask import Flask

from src.models import *
from .views import main


def create_app(config_file: str = "settings.py") -> Flask:
    app = Flask(__name__)
    app.config.from_pyfile(config_file)
    app.register_blueprint(main)

    db.init_app(app)
    migrate.init_app(app, db)

    with app.app_context():
        db.create_all()

    return app
