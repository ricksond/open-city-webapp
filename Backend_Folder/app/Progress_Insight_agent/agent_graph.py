import json
import re
from typing import TypedDict, Optional, List, Dict
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from datetime import datetime, timedelta, timezone  
from .utils import get_llm
from .. import firebase
db = firebase.db
llm = get_llm()

class AnalyticsState(TypedDict, total=False):
    """
    The state for the Analytics Agent.
    """
    uid: str
    saved_recipes: List[Dict] 
    recipe_analytics: Dict 
    recommendation_status: Dict[str, str]
    summary_report: Optional[str]
    error_message: Optional[str]

class EstimatedNutrition(BaseModel):
    """
    Defines the structured output for an LLM
    estimating nutrition from an ingredient list.
    """
    calories: str = Field(description="Estimated calories, e.g., '450 kcal' or 'N/A' if un-estimable.")
    protein: str = Field(description="Estimated protein, e.g., '30 g' or 'N/A'.")
    carbs: str = Field(description="Estimated carbohydrates, e.g., '50 g' or 'N/A'.")
    fat: str = Field(description="Estimated fat, e.g., '20 g' or 'N/A'.")

class AnalyticsDashboard(BaseModel):
    """
    Defines the structured output from the analytics LLM summary.
    This version supports frontend visualizations (trend data, summaries, etc.)
    """
    headline: str = Field(
        description="A catchy, short title (e.g., 'Balanced Protein Week!')."
    )
    primary_insight: str = Field(
        description="Main insight derived from analytics (e.g., 'Average 450 kcal per meal this week.')."
    )
    today_summary: Dict[str, Optional[float | str]] = Field(
        description="Structured data for today's totals, includes count, calories, protein, and message."
    )
    week_summary: Dict[str, Optional[float | str]] = Field(
        description="Structured data for weekly totals, includes count, calories, protein, and message."
    )
    trend_data: Dict[str, List] = Field(
        description="Labels and values for plotting trends (e.g., calories per weekday)."
    )
    recommendation_note: str = Field(
        description="Contextual note connecting the recommendation agent’s focus to the user."
    )

def _parse_nutrition(value_str: str) -> Optional[float]:
    """
    Helper function to parse strings like "550 kcal", "30 g", or "N/A".
    """
    if not isinstance(value_str, str) or value_str.lower() == 'n/a':
        return None
    match = re.search(r'[\d\.]+', value_str)
    if match:
        try:
            return float(match.group(0))
        except (ValueError, TypeError):
            return None
    return None

def fetch_user_recipes(state: AnalyticsState) -> AnalyticsState:
    """
    Node 1: Integrates your first load_state function.
    Fetches saved recipes and their full details from 'dishes'.
    """
    try:
        uid = state.get("uid")
        if not uid:
            raise ValueError("UID must be present in the state.")
        saved_ref = db.collection("userRecipes").document(uid).collection("saved")
        saved_docs = list(saved_ref.stream())
        if not saved_docs:
            return {**state, "saved_recipes": []}
        saved_recipes = []
        for doc in saved_docs:
            saved_data = doc.to_dict()
            recipe_id = saved_data.get("recipe_id")

            if not recipe_id:
                continue
            recipe_doc = db.collection("dishes").document(recipe_id).get()

            if not recipe_doc.exists:
                continue
            recipe_data = recipe_doc.to_dict()
            saved_at_data = saved_data.get("saved_at")
            if isinstance(saved_at_data, datetime):
                saved_at_str = saved_at_data.isoformat()
            else:
                try:
                    saved_at_str = datetime.fromisoformat(str(saved_at_data)).isoformat()
                except Exception:
                    saved_at_str = datetime.now(timezone.utc).isoformat() 
            combined_data = {
                "recipe_id": recipe_id,
                "name": recipe_data.get("name"),
                "ingredients": recipe_data.get("ingredients", []),
                "tags": recipe_data.get("tags", []),
                "metadata": recipe_data.get("metadata", {}),
                "saved_at": saved_at_str,
            }
            saved_recipes.append(combined_data)
        return {**state, "saved_recipes": saved_recipes}
    except Exception as e:
        print(f"Error in fetch_user_recipes: {e}")
        return {**state, "error_message": f"Failed to fetch recipes: {e}"}

def estimate_missing_nutrition(state: AnalyticsState) -> AnalyticsState:
    """
    Node 1.5 (Optimized): Loops through saved recipes and estimates
    missing nutrition, using a cache to avoid re-calling the LLM.
    """
    if state.get("error_message"):
        return state

    try:
        uid = state.get("uid")
        if not uid:
            raise ValueError("UID not in state, cannot check analytics cache.")
        doc_ref = db.collection("userAnalytics").document(uid)
        doc = doc_ref.get()
        cached_recipes_map = {}
        if doc.exists:
            raw_data = doc.to_dict().get("raw", {})
            cached_recipe_details = raw_data.get("recipe_details", [])
            for recipe in cached_recipe_details:
                key = (recipe.get("name"), recipe.get("created_at"))
                cached_recipes_map[key] = recipe.get("metadata", {})
        saved_recipes = state.get("saved_recipes", [])
        if not saved_recipes:
            return state  
        schema = EstimatedNutrition.model_json_schema()
        structured_llm = llm.bind(response_schema=schema)
        enriched_recipes = []
        for recipe in saved_recipes:
            metadata = recipe.get("metadata", {}).copy() 
            ingredients = recipe.get("ingredients", [])
            calorie_value = _parse_nutrition(metadata.get("calories"))
            if calorie_value is None and ingredients:
                saved_at_dt = None
                try:
                    saved_at_raw = recipe.get("saved_at")
                    if isinstance(saved_at_raw, datetime):
                        saved_at_dt = saved_at_raw
                    else:
                        saved_at_dt = datetime.fromisoformat(str(saved_at_raw))
                    if saved_at_dt.tzinfo is None:
                        saved_at_dt = saved_at_dt.replace(tzinfo=timezone.utc)
                    saved_at_iso = saved_at_dt.isoformat()
                except Exception:
                    enriched_recipes.append(recipe)
                    continue

                lookup_key = (recipe.get("name"), saved_at_iso)
                if lookup_key in cached_recipes_map:
                    cached_metadata = cached_recipes_map[lookup_key]
                    metadata["calories"] = f"{cached_metadata.get('calories', 0)} (est.)"
                    metadata["protein"]  = f"{cached_metadata.get('protein', 0)} (est.)"
                    metadata["carbs"]    = f"{cached_metadata.get('carbs', 0)} (est.)"
                    metadata["fat"]      = f"{cached_metadata.get('fat', 0)} (est.)"
                    
                    recipe["metadata"] = metadata
                
                else:
                    prompt = f"""
                    Analyze this ingredient list and estimate its nutritional content
                    for a single serving.
                    
                    Ingredients: {json.dumps(ingredients)}
                    
                    Return your estimates for calories, protein, carbs, and fat.
                    """
                    try:
                        ai_message = structured_llm.invoke(prompt)
                        summary_data = json.loads(ai_message.content)
                        estimates = EstimatedNutrition(**summary_data)
                        
                        metadata["calories"] = f"{estimates.calories} (est.)"
                        metadata["protein"]  = f"{estimates.protein} (est.)"
                        metadata["carbs"]    = f"{estimates.carbs} (est.)"
                        metadata["fat"]      = f"{estimates.fat} (est.)"
                        recipe["metadata"] = metadata

                    except Exception as e:
                        print(f"  > LLM estimation FAILED for {recipe.get('name')}: {e}")
            enriched_recipes.append(recipe)
        return {**state, "saved_recipes": enriched_recipes}
    except Exception as e:
        print(f"Error in estimate_missing_nutrition: {e}")
        return {**state, "error_message": f"Failed to estimate nutrition: {e}"}


def compute_recipe_analytics(state: AnalyticsState) -> AnalyticsState:
    """
    Node 2: Computes advanced, time-based analytics for the dashboard.
    This node now assumes the 'estimate_missing_nutrition' node has
    already run, so it does not skip recipes.
    """
    if state.get("error_message"):
        return state

    try:
        saved_recipes = state.get("saved_recipes", [])
        if not saved_recipes:
            return {
                **state,
                "recipe_analytics": {
                    "timeframes": {
                        "today": {"count": 0},
                        "past_7_days": {"count": 0},
                        "all_time": {"count": 0}
                    },
                    "recipe_details": [],
                }
            }
        nutrients = ["calories", "protein", "carbs", "fat"]
        now = datetime.now(timezone.utc)
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = today_start - timedelta(days=7)

        today_totals = {n: 0 for n in nutrients}
        week_totals = {n: 0 for n in nutrients}
        all_time_values = {n: [] for n in nutrients}
        today_count = 0
        week_count = 0
        recipe_details = []
        for recipe in saved_recipes:
            metadata = recipe.get("metadata", {})
            ingredients = recipe.get("ingredients", [])
            parsed_nutrients = {}
            for nutrient in nutrients:
                value = _parse_nutrition(metadata.get(nutrient))
                if value is None:
                    parsed_nutrients[nutrient] = 0
                else:
                    parsed_nutrients[nutrient] = value
            saved_at_raw = recipe.get("saved_at")
            if not saved_at_raw:
                continue 
            try:
                if isinstance(saved_at_raw, datetime):
                    saved_at_dt = saved_at_raw
                else:
                    saved_at_dt = datetime.fromisoformat(str(saved_at_raw))
                if saved_at_dt.tzinfo is None:
                    saved_at_dt = saved_at_dt.replace(tzinfo=timezone.utc)
            except Exception:
                continue 
            for n in nutrients:
                if parsed_nutrients[n] > 0:
                     all_time_values[n].append(parsed_nutrients[n])
            if saved_at_dt >= week_start:
                week_count += 1
                for n in nutrients:
                    week_totals[n] += parsed_nutrients[n]
            if saved_at_dt >= today_start:
                today_count += 1
                for n in nutrients:
                    today_totals[n] += parsed_nutrients[n]
            recipe_details.append({
                "name": recipe.get("name"),
                "created_at": saved_at_dt.isoformat(),
                "ingredients": ingredients,
                "tags": recipe.get("tags", []),
                "metadata": parsed_nutrients 
            })
        all_time_avg = {}
        for n in nutrients:
            if all_time_values[n]:
                all_time_avg[f"avg_{n}"] = round(sum(all_time_values[n]) / len(all_time_values[n]), 2)
            else:
                all_time_avg[f"avg_{n}"] = 0
        all_time_avg["count"] = len(all_time_values["calories"])
        analytics = {
            "timeframes": {
                "today": {"count": today_count, **today_totals},
                "past_7_days": {"count": week_count, **week_totals},
                "all_time": all_time_avg
            },
            "recipe_details": recipe_details,
        }
        return {**state, "recipe_analytics": analytics}
    except Exception as e:
        print(f"Error in compute_recipe_analytics: {e}")
        return {**state, "error_message": f"Failed to compute analytics: {e}"}


def fetch_recommendation_state(state: AnalyticsState) -> AnalyticsState:
    """
    Node 3: Fetches the agent's 'thinking process' from 'recommendation_states'.
    """
    if state.get("error_message"):
        return state 
    try:
        uid = state.get("uid")
        doc = db.collection("recommendation_states").document(uid).get()
        if doc.exists:
            status = doc.to_dict()
        else:
            status = {"status": "idle", "last_focus": "none"}
        return {**state, "recommendation_status": status}
    except Exception as e:
        print(f"Error in fetch_recommendation_state: {e}")
        return {**state, "error_message": f"Failed to fetch rec state: {e}"}

def generate_analytics_summary(state: AnalyticsState) -> AnalyticsState:
    """
    Node 3: Generates a structured analytics summary for the user's dashboard.
    Produces both human-readable insights (via LLM) and structured metrics 
    (for frontend charts and trend visualizations).
    """
    try:
        analytics = state.get("recipe_analytics", {})
        recipe_details = analytics.get("recipe_details", [])
        status = state.get("recommendation_status", {})

        if not analytics:
            return {**state, "error_message": "No analytics data found."}
        analytics_str = json.dumps(analytics, indent=2)
        status_str = json.dumps(status, indent=2)
        recipe_context = [
            {"name": r.get("name"), "tags": r.get("tags", [])}
            for r in recipe_details
        ]
        recipes_str = json.dumps(recipe_context, indent=2)
        prompt = f"""
        You are an analytics AI for a nutrition tracking app. 
        Your job is to generate a short, structured dashboard summary combining
        numerical analytics and a human-readable insight.

        Here is the analytics data:
        <analytics_data>
        {analytics_str}
        </analytics_data>

        Here is the current system state:
        <recommendation_status>
        {status_str}
        </recommendation_status>

        Here is a list of saved recipes:
        <recipe_context_data>
        {recipes_str}
        </recipe_context_data>

        ---
        Return a JSON matching this schema:
        {{
            "headline": "string - catchy insight title",
            "primary_insight": "string - main takeaway",
            "today_summary": {{
                "count": int,
                "calories": int,
                "protein": int,
                "message": "string summary"
            }},
            "week_summary": {{
                "count": int,
                "calories": int,
                "protein": int,
                "message": "string summary"
            }},
            "trend_data": {{
                "labels": ["Mon","Tue","Wed","Thu","Fri","Sat","Sun"],
                "values": [int, int, int, int, int, int, int]
            }},
            "recommendation_note": "string"
        }}
        """
        schema = AnalyticsDashboard.model_json_schema()
        structured_llm = llm.bind(response_schema=schema)
        ai_message = structured_llm.invoke(prompt)
        summary_data = json.loads(ai_message.content)
        for key in ["today_summary", "week_summary", "trend_data"]:
            val = summary_data.get(key)
            if isinstance(val, str):
                try:
                    summary_data[key] = json.loads(val)
                except Exception:
                    pass 
        summary_obj = AnalyticsDashboard(**summary_data)
        frontend_data = {
            "headline": summary_obj.headline,
            "insight": summary_obj.primary_insight,
            "today": summary_data.get("today_summary", {}),
            "week": summary_data.get("week_summary", {}),
            "trend": summary_data.get("trend_data", {}),
            "recommendation": summary_data.get("recommendation_note", ""),
            "raw": analytics,
        }
        return {
            **state,
            "summary_report": json.dumps(frontend_data, indent=2)
        }
    except Exception as e:
        print(f"Error in generate_analytics_summary: {e}")
        return {**state, "error_message": f"Failed to generate summary: {e}"}

def build_graph():
    """
    Builds the Analytics Agent graph.
    Flow:
    1. Fetch Recipes
    2. Estimate Missing Nutrition (NEW SLOW STEP)
    3. Compute Time-Based Analytics
    4. Fetch Rec Status
    5. Generate Dashboard Summary
    """
    g = StateGraph(AnalyticsState)
    g.add_node("fetch_user_recipes", fetch_user_recipes)
    g.add_node("estimate_missing_nutrition", estimate_missing_nutrition) 
    g.add_node("compute_recipe_analytics", compute_recipe_analytics)
    g.add_node("fetch_recommendation_state", fetch_recommendation_state)
    g.add_node("generate_analytics_summary", generate_analytics_summary)
    g.set_entry_point("fetch_user_recipes")
    g.add_edge("fetch_user_recipes", "estimate_missing_nutrition") 
    g.add_edge("estimate_missing_nutrition", "compute_recipe_analytics")
    g.add_edge("compute_recipe_analytics", "fetch_recommendation_state")
    g.add_edge("fetch_recommendation_state", "generate_analytics_summary")
    g.add_edge("generate_analytics_summary", END)

    return g.compile()

analytics_agent = build_graph()