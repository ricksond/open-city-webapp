from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
import traceback

profile_bp = Blueprint("profile", __name__, url_prefix="/profile")


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid (expected: Bearer <token>)"}), 401

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Authorization token missing"}), 401
        try:
            decoded = current_app.auth.verify_id_token(token)
            uid = decoded.get("uid") or decoded.get("user_id") or decoded.get("sub")
            if not uid:
                return jsonify({"error": "Invalid token (no uid)"}), 401
            g.uid = uid
        except Exception as e:
            print(f"Auth error: {e}")
            return jsonify({"error": "Invalid or expired token"}), 401

        return f(*args, **kwargs)
    return wrapper

def user_collection():
    return current_app.db.collection("users")

def _require_body_uid_matches_token(body_uid):
    if body_uid is None:
        return True, None
    if str(body_uid) != str(g.uid):
        return False, (jsonify({"error": "UID mismatch between token and request body"}), 401)
    return True, None


def _require_query_uid_matches_token(query_uid):
    if query_uid is None:
        return True, None
    if str(query_uid) != str(g.uid):
        return False, (jsonify({"error": "UID mismatch between token and query parameter"}), 401)
    return True, None


@profile_bp.route("", methods=["GET"])
@require_auth
def get_profile():
    try:
        uid = g.uid
        query_uid = request.args.get("uid")
        ok, resp = _require_query_uid_matches_token(query_uid)
        if not ok:
            return resp

        doc = user_collection().document(uid).get()
        profile = doc.to_dict() or {}

        return jsonify({"uid": uid, "profile": profile}), 200

    except Exception:
        print("Error in get_profile:", traceback.format_exc())
        return jsonify({"error": "Failed to fetch profile"}), 500



@profile_bp.route("", methods=["POST"])
@require_auth
def update_profile():
    try:
        payload = request.get_json() or {}
        if not payload:
            return jsonify({"error": "Empty request body"}), 400
        body_uid = payload.get("uid")
        ok, resp = _require_body_uid_matches_token(body_uid)
        if not ok:
            return resp
        uid = g.uid
        user_collection().document(uid).set(payload, merge=True)
        return jsonify({"message": "Profile updated", "uid": uid}), 200

    except Exception:
        print("Error in update_profile:", traceback.format_exc())
        return jsonify({"error": "Failed to update profile"}), 500
