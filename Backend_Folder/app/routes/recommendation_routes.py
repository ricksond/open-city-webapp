import json
import logging
from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
from ..recommendation_agent.agent_graph import recommendation_agent, Recommendation, save_state, load_state
from ..recipe_chat_agent.agent_graph import recipe_app
from .. import firebase


db = firebase.db
recommendations_bp = Blueprint(
    "recommendations", __name__, url_prefix="/recommendations")




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
            uid = decoded.get("uid") or decoded.get(
                "user_id") or decoded.get("sub")
            if not uid:
                return jsonify({"error": "Invalid token (no uid)"}), 401
            g.uid = uid
        except Exception as e:
            return jsonify({"error": "Invalid or expired token", "details": str(e)}), 401
        return f(*args, **kwargs)
    return wrapper


@recommendations_bp.route("", methods=["POST"])
@require_auth
def generate_recommendation():
    uid = g.uid
    body = request.get_json(silent=True) or {}
    print("body", body)
    state = load_state(uid) or {
        "uid": uid,
        "user_profile": {},
        "recommendation_request": body.get("recommendation_request", ""),
        "feedback": body.get("feedback"),
        "bot_response": "",
        "history": []
    }
    user_doc = db.collection("users").document(uid).get()
    if user_doc.exists:
        user_data = user_doc.to_dict() or {}
        user_prefs = user_data.get("user_preferences", {"liked_tags": {}, "disliked_tags": {}})
        user_cuisines = user_data.get("cuisine", "")
        user_diet = user_data.get("diet", "")
        user_allergies = user_data.get("allergies", "")
    else:
        user_prefs = {"liked_tags": {}, "disliked_tags": {}}
        user_cuisines = ""
        user_diet = ""
        user_allergies = ""
    user_profile = state.get("user_profile", {})
    incoming_profile = body.get("user_profile", {})
    incoming_user_prefs = incoming_profile.get("user_preferences", {})
    merged_liked_tags = incoming_user_prefs.get(
        "liked_tags", user_prefs.get("liked_tags", {}))
    merged_disliked_tags = incoming_user_prefs.get(
        "disliked_tags", user_prefs.get("disliked_tags", {}))
    user_profile_updated = {
        **user_profile,
        **incoming_profile,
        "user_preferences": {
            "liked_tags": merged_liked_tags,
            "disliked_tags": merged_disliked_tags
        },
        "recommendation_request_time":body.get("Recommendation_time"),
        "cuisine": user_cuisines,
        "diet": user_diet,
        "allergies": user_allergies
    }

    state["user_profile"] = user_profile_updated
    new_state = recommendation_agent.invoke(state)
    save_state(uid, new_state)

    bot_reply = json.loads(new_state.get(
        "bot_response", "{}")).get("reply", "")
    rec = new_state.get("current_recommendation")
    rec_out = rec.dict() if hasattr(rec, "dict") else rec

    return jsonify({
        "message": bot_reply,
        "recommendation": rec_out
    }), 200


@recommendations_bp.route("/accept", methods=["POST"])
@require_auth
def accept_recommendation():
    uid = g.uid

    state = load_state(uid)
    if not state or not state.get("current_recommendation"):
        return jsonify({"error": "No active recommendation"}), 400
    state["feedback"] = "" 
    user_profile = state.get("user_profile") or {}
    user_profile["feedback"] = [] 
    state["user_profile"] = user_profile
    save_state(uid, state)
    recommendation = state["current_recommendation"]
    if isinstance(recommendation, dict):
        recommendation = Recommendation(**recommendation)
    meal = recommendation.meal
    meal_name = meal.name if hasattr(meal, "name") else meal.get("name")
    recipe_state = {
        "user_message": None,
        "recipe_request": meal_name,
        "missing_ingredients": [],
        "current_recipe": None,
        "current_step_index": -1,
        "bot_response": "",
        "history": []
    }

    recipe_result = recipe_app.invoke(recipe_state)
    recipe_reply = json.loads(recipe_result.get(
        "bot_response", "{}")).get("reply", "")
    recipe = recipe_result.get("current_recipe")
    return jsonify({
        "message": f"Accepted meal '{meal_name}'. {recipe_reply}",
        "recipe": recipe.dict() if recipe else None
    }), 200


@recommendations_bp.route("/reject", methods=["POST"])
@require_auth
def reject_recommendation():
    uid = g.uid
    body = request.get_json(silent=True) or {}
    reason = body.get("reason", "")

    if not reason:
        return jsonify({"error": "Please provide a rejection reason"}), 400

    state = load_state(uid) or {}

    user_profile = state.get("user_profile") or {}
    print("User Profile from reject", user_profile)
    existing_feedback = user_profile.get("feedback") or []
    if not isinstance(existing_feedback, list):
        existing_feedback = [existing_feedback] if existing_feedback else []
    print("existing feedback", existing_feedback)
    print("Reason", reason)
    existing_feedback.append(reason)
    print("existing feedback", existing_feedback)
    print("Existing state", state)
    print("User_profile", user_profile)
    state["user_profile"]["feedback"]= existing_feedback
    state["recommendation_request"] = ""  
    state["uid"] = uid
    new_state = recommendation_agent.invoke(state)
    save_state(uid, new_state)
    rec = new_state.get("current_recommendation")
    bot_reply = new_state.get("bot_response", "")

    try:
        bot_reply_json = json.loads(bot_reply)
        bot_reply_text = bot_reply_json.get("reply", "")
    except Exception:
        bot_reply_text = bot_reply if isinstance(bot_reply, str) else ""

    rec_out = rec.dict() if hasattr(rec, "dict") else rec

    return jsonify({
        "message": f"Regenerated recommendation after feedback: {bot_reply_text}",
        "recommendation": rec_out
    }), 200
