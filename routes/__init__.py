"""
Flask blueprints for API routes.

Organizes endpoints into separate modules:
- chat.py: POST /chat (conversational design assistant)
- health.py: GET /health, GET /api/providers (system status)
- vision.py: POST /analyze-image (fabric image analysis)
"""

from flask import Blueprint

def register_routes(app):
    """Register all route blueprints with Flask app."""
    from routes.chat import chat_bp
    from routes.health import health_bp
    from routes.vision import vision_bp
    
    app.register_blueprint(chat_bp)
    app.register_blueprint(health_bp)
    app.register_blueprint(vision_bp)


__all__ = ["register_routes"]
