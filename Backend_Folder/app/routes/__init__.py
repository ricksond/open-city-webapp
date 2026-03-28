from .auth_routes import auth_bp
from .information_routes import info_bp
from .pdf_scan_routes import pdf_bot_bp


def register_blueprints(app):
    """
    Register all blueprints to the Flask app.
    """
    app.register_blueprint(auth_bp)       # /auth
    app.register_blueprint(info_bp)
    app.register_blueprint(pdf_bot_bp)
