import json
from flask import Blueprint, request, jsonify, g
from functools import wraps
from app.recipe_chat_agent.agent_graph import recipe_app, Recipe
from .. import firebase

db = firebase.db
recipe_chat_bp = Blueprint("recipe_chat", __name__, url_prefix="/recipe_chat")


def require_auth(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        print(auth_header)
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid (expected: Bearer <token>)"}), 401
        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Authorization token missing"}), 401
        g.uid = token
        return f(*args, **kwargs)
    return wrapper


def save_state(uid, state):
    try:
        state_dict = dict(state)
        if state_dict.get('current_recipe') and hasattr(state_dict['current_recipe'], 'model_dump'):
            state_dict['current_recipe'] = state_dict['current_recipe'].model_dump()
        db.collection('recipe_states').document(uid).set(state_dict)
    except Exception as e:
        print(f"Error saving state: {e}")
        return {"error": "Failed to save recipe state."}


def load_state(uid):
    try:
        doc = db.collection('recipe_states').document(uid).get()
        if doc.exists:
            state_dict = doc.to_dict()
            if state_dict.get('current_recipe'):
                state_dict['current_recipe'] = Recipe(**state_dict['current_recipe'])
            return state_dict
        return None
    except Exception as e:
        print(f"Error loading state: {e}")
        return {"error": "Failed to load recipe state."}

@recipe_chat_bp.route("/start", methods=["POST"])
@require_auth
def start_chat():
    try:
        data = request.json or {}
        recipe_request = data.get("recipe_request", "pancakes")

        state = {
            "user_message": None,
            "recipe_request": recipe_request,
            "missing_ingredients": [],
            "current_recipe": None,
            "current_step_index": -1,
            "bot_response": "",
            "history": []
        }
        config = {"configurable": {"thread_id": g.uid}}

        final_state = recipe_app.invoke(state, config=config)
        save_result = save_state(g.uid, final_state)
        if isinstance(save_result, dict) and save_result.get("error"):
            return jsonify(save_result), 500

        bot_response = final_state.get("bot_response")
        if bot_response is None:
            return jsonify({"error": "Bot response missing."}), 500
        bot_json = {}
        if isinstance(bot_response, str):
            try:
                bot_json = json.loads(bot_response)
            except (json.JSONDecodeError, TypeError):
                bot_json = {"reply": bot_response}
        elif isinstance(bot_response, dict):
            bot_json = bot_response
        else:
            bot_json = {"reply": str(bot_response)}
        cr = final_state.get("current_recipe")
        if cr:
            try:
                if hasattr(cr, "model_dump"):
                    cr_obj = cr.model_dump()
                elif hasattr(cr, "dict"):
                    cr_obj = cr.dict()
                else:
                    cr_obj = {
                        "title": getattr(cr, "title", None),
                        "ingredients": getattr(cr, "ingredients", None),
                        "steps": getattr(cr, "steps", None),
                        "metadata": getattr(cr, "metadata", None),
                        "image_url": getattr(cr, "image_url", None),
                    }
            except Exception:
                cr_obj = None

            if cr_obj:
                bot_json["current_recipe"] = cr_obj
        bot_json["current_step_index"] = final_state.get("current_step_index", -1)
        return jsonify(bot_json)
    except Exception as e:
        print(f"Error in /start: {e}", flush=True)
        return jsonify({"error": "Internal server error occurred while starting chat."}), 500


@recipe_chat_bp.route("/message", methods=["POST"])
@require_auth
def message_chat():
    try:
        data = request.json or {}
        user_message = data.get("message")
        if not user_message:
            return jsonify({"error": "message field is required"}), 400
        loaded_state = load_state(g.uid)
        if isinstance(loaded_state, dict) and loaded_state.get("error"):
            return jsonify(loaded_state), 500
        if not loaded_state:
            return jsonify({"error": "No existing chat found. Please start a new chat with /start."}), 400

        state_update = {"user_message": user_message}
        updated_state = {**loaded_state, **state_update}
        config = {"configurable": {"thread_id": g.uid}}

        final_state = recipe_app.invoke(updated_state, config=config)
        save_result = save_state(g.uid, final_state)
        if isinstance(save_result, dict) and save_result.get("error"):
            return jsonify(save_result), 500
        bot_response = final_state.get("bot_response")
        if bot_response is None:
            return jsonify({"error": "Bot response missing."}), 500
        bot_json = {}
        if isinstance(bot_response, str):
            try:
                bot_json = json.loads(bot_response)
            except (json.JSONDecodeError, TypeError):
                bot_json = {"reply": bot_response}
        elif isinstance(bot_response, dict):
            bot_json = bot_response
        else:
            bot_json = {"reply": str(bot_response)}
        cr = final_state.get("current_recipe")
        if cr:
            try:
                if hasattr(cr, "model_dump"):
                    cr_obj = cr.model_dump()
                elif hasattr(cr, "dict"):
                    cr_obj = cr.dict()
                else:
                    cr_obj = {
                        "title": getattr(cr, "title", None),
                        "ingredients": getattr(cr, "ingredients", None),
                        "steps": getattr(cr, "steps", None),
                        "metadata": getattr(cr, "metadata", None),
                        "image_url": getattr(cr, "image_url", None),
                    }
            except Exception:
                cr_obj = None
            if cr_obj:
                bot_json["current_recipe"] = cr_obj
        bot_json["current_step_index"] = final_state.get("current_step_index", -1)
        return jsonify(bot_json)
    except Exception as e:
        print(f"Error in /message: {e}", flush=True)
        return jsonify({"error": "Internal server error occurred while processing message."}), 500

