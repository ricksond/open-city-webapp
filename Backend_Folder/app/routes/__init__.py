from .auth_routes import auth_bp
from .information_routes import info_bp


def register_blueprints(app):
    """
    Register all blueprints to the Flask app.
    """
    app.register_blueprint(auth_bp)   
    app.register_blueprint(info_bp)
