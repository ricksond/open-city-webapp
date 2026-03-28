from flask import Blueprint, request, jsonify, session, current_app as app
import json
from firebase_admin import firestore

auth_bp = Blueprint("auth", __name__)

@auth_bp.errorhandler(Exception)
def handle_exceptions(e):
    error_str = str(e)
    print(error_str)
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
    organization_name = data.get("organization_name")
    
    if not email or not password:
        return jsonify({
            "error": {
                "message": "EMAIL_PASSWORD_ORG_REQUIRED"
            }
        }), 400

    user = app.pb_auth.create_user_with_email_and_password(email, password)
    uid = user['localId']
    id_token = user['idToken']
    app.db.collection("users").document(uid).set({
        "email": email,
        "organization_name": organization_name,
        "created_at": firestore.SERVER_TIMESTAMP
    })
    session['organization_name'] = organization_name
    return jsonify({
        "message": "User registered",
        "uid": uid,
        "idToken": id_token,
        "organization_name": organization_name
    }), 201


@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    email = data.get("email")
    password = data.get("password")
    if not email or not password:
        return jsonify({"error": {"message": "EMAIL_AND_PASSWORD_REQUIRED"}}), 400
    user = app.pb_auth.sign_in_with_email_and_password(email, password)
    uid = user['localId']
    user_doc = app.db.collection("users").document(uid).get()
    organization_name = None
    if user_doc.exists:
        organization_name = user_doc.to_dict().get("organization_name")
        session['organization_name'] = organization_name
    return jsonify({
        "message": "Login success",
        "idToken": user['idToken'],
        "uid": uid,
        "organization_name": organization_name
    }), 200

@auth_bp.route('/logout', methods=['POST'])
def logout():
    session.pop('organization_name', None)
    return jsonify({"message": "Logged out"}), 200