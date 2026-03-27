from .auth_routes import auth_bp
from .profile_routes import profile_bp
from .recipe_routes import recipes_bp
from .recipe_chat_routes import recipe_chat_bp
from .dish_preference_routes import dish_bp
from .recommendation_routes import recommendations_bp
from .analytics_routes import analytics_bp
from .habit_routes import habit


def register_blueprints(app):
    """
    Register all blueprints to the Flask app.
    """
    app.register_blueprint(auth_bp)       # /auth
    app.register_blueprint(profile_bp)    # /profile
    app.register_blueprint(recipes_bp)    # /recipes
    app.register_blueprint(recipe_chat_bp)  # /recipe_chat
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(dish_bp) # /dish_preference
    app.register_blueprint(analytics_bp)
    app.register_blueprint(habit)
