"""Flask application for Empirica Outreach API"""

import logging
from flask import Flask, jsonify

logger = logging.getLogger(__name__)


def create_app() -> Flask:
    """Create and configure Flask application"""
    
    app = Flask(
        __name__,
        static_folder='./static',
        template_folder='./templates'
    )
    
    # Enable CORS
    @app.after_request
    def add_cors_headers(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = '*'
        return response
    
    # Health check
    @app.route("/health", methods=["GET"])
    def health_check():
        return jsonify({"status": "ok", "service": "empirica-outreach-api"})
    
    # Register blueprints
    from .routes import bp as outreach_bp
    app.register_blueprint(outreach_bp, url_prefix="/api/v1/outreach")
    
    # Global error handler
    @app.errorhandler(Exception)
    def handle_error(error):
        logger.error(f"API error: {error}")
        return jsonify({
            "ok": False,
            "error": "internal_server_error",
            "message": str(error),
            "status_code": 500
        }), 500
    
    logger.info("✅ Empirica Outreach API initialized")
    return app


if __name__ == "__main__":
    app = create_app()
    app.run(host="0.0.0.0", port=8001, debug=True)
