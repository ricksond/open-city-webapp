import json
from flask import Blueprint, request, jsonify, g
from functools import wraps
from app.Progress_Insight_agent.agent_graph import analytics_agent, AnalyticsState
from .. import firebase

db = firebase.db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/analytics")


def require_auth(f):
    """
    Your provided authentication decorator.
    This gets the UID from the Bearer token and adds it to 'g.uid'.
    """
    @wraps(f)
    def wrapper(*args, **kwargs):
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Authorization header missing or invalid (expected: Bearer <token>)"}), 401
        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return jsonify({"error": "Authorization token missing"}), 401
        g.uid = token
        return f(*args, **kwargs)
    return wrapper


@analytics_bp.route("/get_summary", methods=["GET"])
@require_auth
def get_analytics_summary():
    """
    Runs the analytics agent for the authenticated user,
    stores/updates it in Firestore under 'userAnalytics/<uid>',
    and returns the stored summary.
    """
    try:
        initial_state = {
            "uid": g.uid,
            "saved_recipes": [],
            "recipe_analytics": {},
            "recommendation_status": {},
            "summary_report": None,
            "error_message": None
        }

        config = {"configurable": {"thread_id": g.uid}}
        final_state = analytics_agent.invoke(initial_state, config=config)
        if final_state.get("error_message"):
            print(f"Agent error for uid {g.uid}: {final_state['error_message']}")
            return jsonify({"error": final_state["error_message"]}), 500
        summary_report_json = final_state.get("summary_report")
        if not summary_report_json:
            print(f"No summary report generated for uid {g.uid}.")
            return jsonify({"error": "Failed to generate analytics summary."}), 500
        try:
            summary_data = json.loads(summary_report_json)
        except (json.JSONDecodeError, TypeError) as e:
            print(f"Error parsing summary JSON: {e}")
            return jsonify({"error": "Failed to parse summary data."}), 500
        user_ref = db.collection("userAnalytics").document(g.uid)
        user_ref.set(summary_data, merge=True)
        print(f"Analytics summary stored/updated for UID: {g.uid}")
        return jsonify(summary_data), 200
    except Exception as e:
        print(f"Error in /get_summary: {e}")
        return jsonify({"error": "Internal server error occurred while generating analytics."}), 500


@analytics_bp.route("/get_info", methods=["GET"])
@require_auth
def get_analytics_info():
    """
    Retrieves stored analytics info for a specific user (uid) from Firestore.
    """
    try:
        doc_ref = db.collection("userAnalytics").document(g.uid)
        doc = doc_ref.get()
        if not doc.exists:
            return jsonify({"error": "No analytics data found for this user."}), 404
        return jsonify(doc.to_dict()), 200
    except Exception as e:
        print(f"Error fetching analytics for {g.uid}: {e}")
        return jsonify({"error": "Failed to retrieve analytics info."}), 500