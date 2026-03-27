import json
from flask import Blueprint, request, jsonify, g
from functools import wraps
from app.dish_preference_agent.agent_graph import dish_agent, Dish, load_state, save_state, ensure_pref_shape
from .. import firebase


db = firebase.db
dish_bp = Blueprint("dish_chat", __name__, url_prefix="/dish_chat")


@dish_bp.errorhandler(Exception)
def handle_dish_exceptions(e):
    error_str = str(e)
    error_message = "UNKNOWN_ERROR"

    if "PERMISSION_DENIED" in error_str:
        error_message = "PERMISSION_DENIED"
    elif "INVALID_ARGUMENT" in error_str:
        error_message = "INVALID_ARGUMENT"
    elif "NOT_FOUND" in error_str:
        error_message = "NOT_FOUND"
    elif "UNAUTHENTICATED" in error_str:
        error_message = "UNAUTHENTICATED"
    elif "FIREBASE_ERROR" in error_str:
        error_message = "FIREBASE_ERROR"
    elif "JSONDecodeError" in error_str:
        error_message = "INVALID_JSON"
    elif "KeyError" in error_str:
        error_message = "MISSING_KEY"
    elif "TypeError" in error_str:
        error_message = "TYPE_ERROR"
    elif "ValueError" in error_str:
        error_message = "INVALID_VALUE"

    print(f"[dish_bp] Error: {error_str}")
    return jsonify({"error": {"message": error_message}}), 205


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid"}), 401
        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Authorization token missing"}), 401
        g.uid = token
        return f(*args, **kwargs)
    return wrapper

@dish_bp.route("/start", methods=["POST"])
@require_auth
def start_dish_chat():
    try:
        user_doc = db.collection("users").document(g.uid).get()
        if user_doc.exists:
            user_data = user_doc.to_dict()
            loaded_prefs = ensure_pref_shape(
                user_data.get("user_preferences", {})
            )
        else:
            loaded_prefs = ensure_pref_shape({})
    except Exception as e:
        print(f"Error loading user doc {g.uid}: {e}")
        loaded_prefs = ensure_pref_shape({})
    state = {
        "uid": g.uid,
        "user_message": None,
        "current_dish": None,
        "preference_action": None,
        "user_preferences": loaded_prefs,
        "bot_response": "",
        "history": [],
    }
    config = {"configurable": {"thread_id": g.uid}}
    final_state = dish_agent.invoke(state, config=config)
    save_state(g.uid, final_state)
    print(final_state["bot_response"])
    try:
        return jsonify(json.loads(final_state["bot_response"]))
    except (json.JSONDecodeError, TypeError):
        return jsonify({"reply": final_state["bot_response"]})

@dish_bp.route("/message", methods=["POST"])
@require_auth
def message_dish_chat():
    data = request.json or {}
    user_message = data.get("message")
    if not user_message:
        return jsonify({"error": "message field is required"}), 400
    loaded_state = load_state(g.uid)
    if not loaded_state:
        print(f"No state found for {g.uid}, starting new chat.")
        return start_dish_chat()
    loaded_state["user_preferences"] = ensure_pref_shape(
        loaded_state.get("user_preferences", {})
    )
    updated_state = {
        **loaded_state,
        "user_message": user_message,
        "uid": g.uid
    }
    config = {"configurable": {"thread_id": g.uid}}
    final_state = dish_agent.invoke(updated_state, config=config)
    save_state(g.uid, final_state)
    try:
        return jsonify(json.loads(final_state["bot_response"]))
    except (json.JSONDecodeError, TypeError):
        return jsonify({"reply": final_state["bot_response"]})
