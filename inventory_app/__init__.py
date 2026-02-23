"""Inventory forecasting Flask application factory."""

from flask import Flask

from inventory_app.config import Config
from inventory_app.routes.api import api_bp
from inventory_app.routes.web import web_bp


def create_app(config_object=Config):
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static",
    )
    app.config.from_object(config_object)

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    return app
