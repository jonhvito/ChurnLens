"""Flask application factory."""
from __future__ import annotations

from flask import Flask


def create_app() -> Flask:
    """
    Create and configure Flask application.
    
    Returns:
        Configured Flask app
    """
    app = Flask(
        __name__,
        template_folder="../templates",
        static_folder="../static"
    )
    
    # Load config
    from app import config
    app.config["DEBUG"] = config.DEBUG
    
    # Register blueprints
    from app.web import web
    from app.api import api, export
    
    app.register_blueprint(web)
    app.register_blueprint(api)
    app.register_blueprint(export)
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Not found"}, 404
    
    @app.errorhandler(500)
    def internal_error(e):
        return {"error": "Internal server error"}, 500
    
    return app
