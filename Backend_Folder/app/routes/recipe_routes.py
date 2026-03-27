from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
import random
import traceback
from google.cloud import firestore

recipes_bp = Blueprint("recipes", __name__, url_prefix="/recipes")


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


def recipes_collection():
    return current_app.db.collection("dishes")


def user_recipes_collection(uid):
    return current_app.db.collection("userRecipes").document(uid).collection("saved")


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


@recipes_bp.route("", methods=["GET"])
def list_recipes():
    try:
        search_name = request.args.get("name")
        query = recipes_collection()

        if search_name:
            search_lower = search_name.lower()
            query = query.where("name_lowercase", ">=", search_lower).where(
                "name_lowercase", "<=", search_lower + '\uf8ff'
            )

        docs = query.stream()
        result = []
        for d in docs:
            data = d.to_dict() or {}
            data["id"] = d.id
            result.append(data)

        return jsonify(result), 200
    except Exception as e:
        print("Error in list_recipes:", traceback.format_exc())
        return jsonify({"error": "Failed to fetch recipes"}), 500


@recipes_bp.route("", methods=["POST"])
@require_auth
def create_recipe():
    try:
        data = request.get_json() or {}
        if not data:
            return jsonify({"error": "Empty request body"}), 400

        name = data.get("name")
        if not name or not isinstance(name, str):
            return jsonify({"error": "Dish 'name' is required and must be a string"}), 400

        ingredients = data.get("ingredients")
        if not ingredients or not isinstance(ingredients, list) or not all(isinstance(i, str) for i in ingredients):
            return jsonify({"error": "Dish 'ingredients' must be a list of strings"}), 400

        steps = data.get("steps") or data.get("instructions")
        if not steps or not isinstance(steps, list) or not all(isinstance(i, str) for i in steps):
            return jsonify({"error": "Dish 'steps' or 'instructions' must be a list of strings"}), 400

        metadata = data.get("metadata", {})
        if not isinstance(metadata, dict):
            return jsonify({"error": "'metadata' must be an object"}), 400

        cuisine = data.get("cuisine", metadata.get("cuisine", "Unknown"))
        description = data.get("description", metadata.get("description", ""))
        difficulty = data.get("difficulty", metadata.get("difficulty", "N/A"))
        cook_time = data.get("cook_time", metadata.get("cook_time", "N/A"))
        prep_time = data.get("prep_time", metadata.get("prep_time", "N/A"))
        servings = data.get("servings", metadata.get("servings", 0))
        rating = data.get("rating", metadata.get("rating", 0))
        tags = data.get("tags", [])

        if isinstance(cuisine, str) and cuisine not in tags:
            tags.append(cuisine)
        body_uid = data.get("uid")
        ok, resp = _require_body_uid_matches_token(body_uid)
        if not ok:
            return resp
        uid = g.uid

        dish_data = {
            "name": name.strip(),
            "name_lowercase": name.strip().lower(),
            "ingredients": [i.strip() for i in ingredients],
            "steps": steps,
            "created_by": uid,
            "tags": tags,
            "metadata": {
                "cuisine": cuisine,
                "description": description,
                "difficulty": difficulty,
                "cook_time": cook_time,
                "prep_time": prep_time,
                "servings": int(servings) if str(servings).isdigit() else 0,
                "rating": float(rating) if isinstance(rating, (int, float)) else 0.0,
            },
            "created_at": firestore.SERVER_TIMESTAMP,
            "image_url": data.get("image_url"),
        }

        _, ref = recipes_collection().add(dish_data)
        new_id = ref.id

        return jsonify({"message": "Dish created", "id": new_id}), 201

    except Exception as e:
        print("Error in create_recipe:", traceback.format_exc())
        return jsonify({"error": "Failed to create dish"}), 500


@recipes_bp.route("/<recipe_id>", methods=["GET"])
def get_recipe(recipe_id):
    try:
        doc = recipes_collection().document(recipe_id).get()
        if not doc.exists:
            return jsonify({"error": "Dish not found"}), 404
        data = doc.to_dict() or {}
        data["id"] = doc.id
        return jsonify(data), 200
    except Exception as e:
        print("Error in get_recipe:", traceback.format_exc())
        return jsonify({"error": "Failed to fetch dish"}), 500


@recipes_bp.route("/<recipe_id>", methods=["PUT"])
@require_auth
def update_recipe(recipe_id):
    try:
        payload = request.get_json() or {}
        if not payload:
            return jsonify({"error": "Empty request body"}), 400

        body_uid = payload.get("uid")
        ok, resp = _require_body_uid_matches_token(body_uid)
        if not ok:
            return resp

        uid = g.uid
        doc_ref = recipes_collection().document(recipe_id)
        if not doc_ref.get().exists:
            return jsonify({"error": "Dish not found"}), 404

        payload.setdefault("last_updated_by", uid)
        payload.setdefault("last_updated_at", firestore.SERVER_TIMESTAMP)

        if "name" in payload and isinstance(payload["name"], str):
            payload["name_lowercase"] = payload["name"].lower()

        if "metadata" in payload:
            existing_doc = doc_ref.get().to_dict()
            existing_meta = existing_doc.get("metadata", {})
            existing_meta.update(payload["metadata"])
            payload["metadata"] = existing_meta

        doc_ref.set(payload, merge=True)
        return jsonify({"message": "Dish updated", "id": recipe_id}), 200
    except Exception as e:
        print("Error in update_recipe:", traceback.format_exc())
        return jsonify({"error": "Failed to update dish"}), 500


@recipes_bp.route("/<recipe_id>", methods=["DELETE"])
@require_auth
def delete_recipe(recipe_id):
    try:
        body = request.get_json(silent=True) or {}
        body_uid = body.get("uid")
        ok, resp = _require_body_uid_matches_token(body_uid)
        if not ok:
            return resp

        doc_ref = recipes_collection().document(recipe_id)
        if not doc_ref.get().exists:
            return jsonify({"error": "Dish not found"}), 404

        doc_ref.delete()
        return jsonify({"message": "Dish deleted", "id": recipe_id}), 200
    except Exception as e:
        print("Error in delete_recipe:", traceback.format_exc())
        return jsonify({"error": "Failed to delete dish"}), 500


def _save_recipe_for_user_logic():
    try:
        body = request.get_json() or {}
        body_uid = body.get("uid")
        ok, resp = _require_body_uid_matches_token(body_uid)
        if not ok:
            return resp

        uid = g.uid
        recipe_id = body.get("recipe_id")
        if not recipe_id:
            return jsonify({"error": "recipe_id is required"}), 400

        recipe_doc = recipes_collection().document(recipe_id).get()
        if not recipe_doc.exists:
            return jsonify({"error": "Dish not found in global DB"}), 404

        saved_ref = user_recipes_collection(uid).document(recipe_id)
        saved_ref.set({
            "recipe_id": recipe_id,
            "saved_at": firestore.SERVER_TIMESTAMP,
            "saved_by": uid
        })
        return jsonify({"message": "Dish saved for user", "recipe_id": recipe_id}), 201
    except Exception as e:
        print("Error in _save_recipe_for_user_logic:", traceback.format_exc())
        return jsonify({"error": "Failed to save dish for user"}), 500


def _list_user_saved_recipes_logic():
    try:
        query_uid = request.args.get("uid")
        ok, resp = _require_query_uid_matches_token(query_uid)
        if not ok:
            return resp

        uid = g.uid
        saved_docs = list(user_recipes_collection(uid).stream())
        if not saved_docs:
            return jsonify([]), 200

        recipes = []
        for doc_snapshot in saved_docs:
            saved_data = doc_snapshot.to_dict()
            if not saved_data:
                continue

            recipe_id = saved_data.get("recipe_id") or doc_snapshot.id
            if not recipe_id:
                continue
            recipe_snapshot = recipes_collection().document(recipe_id).get()
            if not recipe_snapshot.exists:
                continue

            recipe_data = recipe_snapshot.to_dict() or {}
            recipe_data.update({
                "id": recipe_snapshot.id,
                "saved_at": saved_data.get("saved_at"),
                "saved_by": saved_data.get("saved_by")
            })
            recipes.append(recipe_data)

        return jsonify(recipes), 200
    except Exception as e:
        print("Error in _list_user_saved_recipes_logic:", traceback.format_exc())
        return jsonify({"error": "Failed to list saved dishes"}), 500


def _delete_user_saved_recipe_logic(recipe_id):
    try:
        body = request.get_json(silent=True) or {}
        body_uid = body.get("uid")
        ok, resp = _require_body_uid_matches_token(body_uid)
        if not ok:
            return resp

        uid = g.uid
        saved_doc_ref = user_recipes_collection(uid).document(recipe_id)
        if not saved_doc_ref.get().exists:
            return jsonify({"error": "Saved dish not found"}), 404

        saved_doc_ref.delete()
        return jsonify({"message": "Saved dish removed", "recipe_id": recipe_id}), 200
    except Exception as e:
        print("Error in _delete_user_saved_recipe_logic:", traceback.format_exc())
        return jsonify({"error": "Failed to remove saved dish"}), 500


@recipes_bp.route("/my/recipes", methods=["POST"])
@require_auth
def save_recipe_for_user():
    return _save_recipe_for_user_logic()


@recipes_bp.route("/my/recipes", methods=["GET"])
@require_auth
def list_user_saved_recipes():
    return _list_user_saved_recipes_logic()


@recipes_bp.route("/my/recipes/<recipe_id>", methods=["DELETE"])
@require_auth
def delete_user_saved_recipe(recipe_id):
    return _delete_user_saved_recipe_logic(recipe_id)


@recipes_bp.route("/history", methods=["GET"])
@require_auth
def user_history():
    return _list_user_saved_recipes_logic()


@recipes_bp.route("/history", methods=["POST"])
@require_auth
def save_recipe_to_history():
    return _save_recipe_for_user_logic()


@recipes_bp.route("/history/<recipe_id>", methods=["DELETE"])
@require_auth
def delete_recipe_from_history(recipe_id):
    return _delete_user_saved_recipe_logic(recipe_id)


@recipes_bp.route("/recommendations", methods=["GET"])
@require_auth
def recommendations():
    """Generate personalized recipe recommendations for the authenticated user."""
    try:
        uid = g.uid
        from ..recommendation_agent.agent_graph import recommendation_app, Recommendation
        user_recs = Recommendation.get_user_recommendations(uid)
        return jsonify(user_recs), 200
    except Exception as e:
        print("Error in recommendations:", traceback.format_exc())
        return jsonify({"error": "Failed to generate recommendations"}), 500
