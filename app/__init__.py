# app/__init__.py

from flask import Flask
from flask_cors import CORS
from .public_api import config_routes, export_routes, bom_routes, supplier_routes

def create_app() -> Flask:
    app = Flask(__name__)
    # Allow WP/Elementor frontend to call /api/*
    CORS(app, resources={r"/api/*": {"origins": "*"}})
    #Debug remove later
    @app.route("/debug/routes")
    def debug_routes():
        return "<pre>" + "\n".join(sorted(str(r) for r in app.url_map.iter_rules())) + "</pre>"

    # Passenger root route check
    @app.route("/")
    def home():
        return "OK"

    # MOUNT API BLUEPRINTS UNDER /api/*
    app.register_blueprint(
        config_routes.config_bp,
        url_prefix="/api/config"
    )

    app.register_blueprint(
        supplier_routes.supplier_bp,
        url_prefix="/api/suppliers"
    )

    app.register_blueprint(
        export_routes.export_bp,
        url_prefix="/api/export"
    )

    app.register_blueprint(
        bom_routes.bom_bp,
        url_prefix="/api/bom"
    )

    return app
