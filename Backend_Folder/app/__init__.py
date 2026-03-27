from flask import Flask
from flask_cors import CORS
import os


def create_app():
    app = Flask(__name__)

    CORS(
        app,
        supports_credentials=True,
        origins=["http://localhost:3000"],
        allow_headers=["Content-Type", "Authorization"],
        expose_headers=["Content-Type", "Authorization"]
    )

    app.secret_key = os.getenv("SESSION_SECRET")

    from .firebase import db, pb_auth, auth
    app.db = db
    app.pb_auth = pb_auth
    app.auth = auth

    from .routes import register_blueprints
    register_blueprints(app)

    return app
