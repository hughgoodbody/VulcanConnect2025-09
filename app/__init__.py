# app/__init__.py

from flask import Flask
from .public_api import config_routes, export_routes, bom_routes


def create_app() -> Flask:
    app = Flask(__name__)

    # Root route required for Passenger health check
    @app.route("/")
    def home():
        return "OK"

    # Register blueprints
    app.register_blueprint(config_routes.config_bp)
    app.register_blueprint(export_routes.export_bp)
    app.register_blueprint(bom_routes.bom_bp)

    return app
