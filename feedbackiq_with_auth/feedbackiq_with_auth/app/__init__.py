"""
app/__init__.py
Flask application factory
"""

import os
from flask import Flask
from config.settings import get_config


def create_app():
    app = Flask(__name__)
    config = get_config()
    app.config.from_object(config)

    os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
    os.makedirs(os.path.dirname(app.config["DB_PATH"]), exist_ok=True)

    # Initialise DB schema (idempotent)
    from app.database.schema import init_db
    init_db(db_path=app.config["DB_PATH"])

    # Blueprints
    from app.routes.main import main_bp
    from app.routes.api  import api_bp
    from app.auth        import auth_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp,  url_prefix="/api")
    app.register_blueprint(auth_bp)

    return app
