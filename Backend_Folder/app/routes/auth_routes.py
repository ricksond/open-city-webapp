from flask import Blueprint, request, jsonify, current_app as app
import json

auth_bp = Blueprint("auth", __name__)

@auth_bp.errorhandler(Exception)
def handle_exceptions(e):
    error_str = str(e)
    firebase_message = "INVALID_EMAIL_OR_PASSWORD"
    if "EMAIL_EXISTS" in error_str:
        firebase_message = "EMAIL_EXISTS"
    elif "INVALID_PASSWORD" in error_str:
        firebase_message = "INVALID_PASSWORD"
    elif "WEAK_PASSWORD" in error_str:
        firebase_message = "WEAK_PASSWORD"
    elif "INVALID_EMAIL" in error_str:
        firebase_message = "INVALID_EMAIL"
    elif "EMAIL_NOT_FOUND" in error_str:
        firebase_message = "EMAIL_NOT_FOUND"
    elif '{' in error_str:
        try:
            error_json = json.loads(error_str[error_str.index('{'):])
            firebase_message = error_json.get("error", {}).get("message", "UNKNOWN_ERROR")
        except Exception:
            firebase_message = "UNKNOWN_ERROR"
    return jsonify({"error": {"message": firebase_message}}), 400


@auth_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    name = data.get("name", "")
    weight = data.get("weight", "")
    preferredFood = data.get("preferredFood", "")
    cuisine = data.get("cuisine", "")
    diet = data.get("diet", "")
    allegories = data.get("allegories", "")
    if not email or not password:
        return jsonify({"error": {"message": "EMAIL_AND_PASSWORD_REQUIRED"}}), 400
    user = app.pb_auth.create_user_with_email_and_password(email, password)
    uid = user['localId']
    id_token = user['idToken']
    app.db.collection("users").document(uid).set({
        "email": email,
        "name": name,
        "weight": weight,
        "preferredFood": preferredFood,
        "cuisine": cuisine,
        "diet": diet,
        "allegories": allegories,
        "user_preferences": {"liked_tags": {}, "disliked_tags": {}},
    })
    return jsonify({"message": "User registered", "uid": uid, "idToken": id_token}), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")

    if not email or not password:
        return jsonify({"error": {"message": "EMAIL_AND_PASSWORD_REQUIRED"}}), 400
    user = app.pb_auth.sign_in_with_email_and_password(email, password)
    return jsonify({
        "message": "Login success",
        "idToken": user['idToken'],
        "uid": user['localId']
    }), 200


@auth_bp.route('/logout', methods=['POST'])
def logout():
    return jsonify({"message": "Logged out"}), 200
