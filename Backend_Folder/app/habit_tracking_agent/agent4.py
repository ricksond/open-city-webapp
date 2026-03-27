import json
from typing import TypedDict,List,Optional,Dict,Any
from pydantic import BaseModel,Field
from langgraph.graph import StateGraph,START,END
from .utils import get_llm
from collections import defaultdict
import statistics

from .. import firebase
from datetime import datetime,timedelta
import re

# initializing DB to get Data
db=firebase.db
llm=get_llm()

class HabitState(TypedDict,total=False):
    uid: Optional[str]
    saved_dishes: List[Dict]
    recommendations:List[Dict]
    analytics:Dict
    habit_summary:Optional[str]
    error_message:Optional[str]

class HabitSummary(BaseModel):
    headline:str
    insights:str
    weekly_trends:Dict[str,float]
    most_liked_tags:List[str]
    most_disliked_tags: List[str]
    recommended_cuisines: List[str]
    total_interactions: int

def safe_load_json(text: str) -> dict:
    try:
        return json.loads(text)
    except Exception:
        return {}
    
def fetch_dish_history(state: HabitState) -> HabitState:
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
        return {**state, "saved_dishes": saved_recipes}
    except Exception as e:
        print(f"Error in fetch_user_recipes: {e}")
        return {**state, "error_message": f"Failed to fetch recipes: {e}"}
    
def fetch_dish_recommendations(state:HabitState)->HabitState:
    """
     Fetches user's recommendations interactions
    """
    print("[NODE] fetch_recommendation_history")
    try:
        uid=state.get("uid")
        if not uid:
            raise ValueError("UID Missing")
        
        doc=db.collection("recommendation_states").document(uid).get()
        if not doc.exists:
            return {**state,"recommendations":[]}
        
        rec_state=doc.to_dict()
        rec_list=[]
        if rec_state.get("current_recommendation"):
            rec_list.append(rec_state["current_recommendation"])
        return {**state,"recommendations":rec_list}
    except Exception as e:
        return {**state,"error_message":f"Failed to get recommendations: {e}"}

def fetch_analytics(state:HabitState)->HabitState:
    """
    Fetches Analytics Summary if any
    """
    print("[NODE] fetch_analytics")
    try:
        uid=state.get("uid")
        if not uid:
            raise ValueError("UID missing")
        
        doc=db.collection("userAnalytics").document(uid).get()
        if doc.exists:
            return {**state,"analytics":doc.to_dict()}
        return {**state,"analytics":{}}
    except Exception as e:
        return {**state,"error_message":f"Failed to fetch user Analytics:{e}"}
# to fetch Patterns
def extract_patterns(state:HabitState) -> HabitState:
    """
    This node helps in extracting realtime patterns based on user data
    """
    print("[NODE] Extract_Patterns")
    saved=state.get("saved_dishes",[])
    if not saved:
        return {**state,"patterns":{}}
    
    calories_by_day=defaultdict(float)
    sugar_by_day=defaultdict(float)
    meal_times=[]
    streak_days=set()

    for dish in saved:
        timestamp=dish.get("saved_at")
        metadata=dish.get("metadata",{})

        try:
            dt=datetime.fromisoformat(timestamp.replace("Z",""))
        except:
            continue

        day=dt.date()
        streak_days.add(day)
        meal_times.append(dt.hour)
        
        # Calories tracking
        cal=metadata.get("calories")
        if cal:
            match=re.search(r"[\d\.]+", str(cal))
            if match:
                calories_by_day[day] +=float(match.group(0))
        
        # Sugar
        sugar=metadata.get("sugar") or metadata.get("carbs")
        if sugar:
            match=re.search(r"[\d\.]+", str(sugar))
            if match:
                sugar_by_day[day] += float(match.group(0))

    # Meal Patterns
    avg_meal_hour = round(sum(meal_times) / len(meal_times), 2)
    late_night_meals = sum(1 for h in meal_times if h >= 21)
    morning_meals = sum(1 for h in meal_times if h < 11)

    # Calorie trends
    daily_kcal_values = list(calories_by_day.values())
    avg_daily_kcal = round(statistics.mean(daily_kcal_values), 2) if daily_kcal_values else 0
    max_spike = max(daily_kcal_values) if daily_kcal_values else 0

    # Sugar trends
    daily_sugar_values = list(sugar_by_day.values())
    avg_daily_sugar = round(statistics.mean(daily_sugar_values), 2) if daily_sugar_values else 0
    sugar_spikes = sum(1 for s in daily_sugar_values if s > 25)

    streak_len=1
    sorted_days=sorted(streak_days)
    longest=1
    for i in range(1,len(sorted_days)):
        if(sorted_days[i] - sorted_days[i-1]).days == 1:
            streak_len+=1
        else:
            longest=max(longest,streak_len)
            streak_len =1
    longest=max(longest,streak_len)

    patterns = {
        "timing": {
            "avg_meal_hour": avg_meal_hour,
            "late_night_meals": late_night_meals,
            "morning_meals": morning_meals,
        },
        "calories": {
            "avg_daily": avg_daily_kcal,
            "max_spike": max_spike,
        },
        "sugar": {
            "avg_daily_sugar": avg_daily_sugar,
            "spike_days": sugar_spikes,
        },
        "tracking": {
            "days_logged": len(streak_days),
            "longest_streak": longest,
        }
    }

    return {**state,"patterns":patterns}
    
    
def generate_habit_summary(state:HabitState)->HabitState:
    """
    Analyzes User patterns and generate human Readable habit summary
    """
    print("[NODE] generate_habit_summary")
    if state.get("error_message"):
        return state
    
    saved_dishes=state.get("saved_dishes",[])
    recommendations=state.get("recommendations",[])
    print("[NODE] generate_habit_summary",saved_dishes,recommendations)
    # Returns an object instead of plain text
    if not saved_dishes and not recommendations:
           summary = {
            "headline": "Not Enough Data Yet",
            "insights": "You have not logged enough meals for analysis.",
            "weekly_trends": {"avg_calories": 0},
            "tags": {"liked": [], "disliked": []},
            "recommended_cuisines": [],
            "totals": {"interactions": 0, "avg_calories": 0},
            "ai_summary": {
                "points": [
                    "No meals logged yet.",
                    "Start tracking meals to generate insights.",
                    "Tag patterns will appear after more interactions.",
                    "Calorie trends unlock after consistent logging."
                ]
            }
        }
           return {
               **state,
               "summary":summary
           }
    
    liked_tags={}
    disliked_tags={}
    cuisines=set()
    calories_list=[]
    # for dish in saved_dishes:
    #     tags=dish.get("current_dish",{}).get("tags",[])
    #     action=dish.get("preference_action")
    #     if action == "like":
    #         for t in tags:
    #             liked_tags[t]=liked_tags.get(t,0)+1
    #     elif action == "dislike":
    #         for t in tags:
    #             disliked_tags[t]=disliked_tags.get(t,0) + 1
        
    #     metadata=dish.get("current_dish",{}).get("metadata",{})
    #     cal=metadata.get("calories")
    #     if cal:
    #         match=re.search(r"[\d\.]+",str(cal))
    #         if match:
    #             calories_list.append(float(match.group(0)))

    #     cuisine=metadata.get("cuisines")
    #     if cuisine:
    #         cuisines.add(cuisine)
    for dish in saved_dishes:
        tags = dish.get("tags", [])
        action = dish.get("preference_action")  # make sure this exists in your data
        if action == "like":
            for t in tags:
                liked_tags[t] = liked_tags.get(t, 0) + 1
        elif action == "dislike":
            for t in tags:
                disliked_tags[t] = disliked_tags.get(t, 0) + 1

        metadata = dish.get("metadata", {})
        cal = metadata.get("calories")
        if cal:
            match = re.search(r"[\d\.]+", str(cal))
            if match:
                calories_list.append(float(match.group(0)))

        cuisine = metadata.get("cuisines")
        if cuisine:
            cuisines.add(cuisine)

        
    avg_calories=round(sum(calories_list)/len(calories_list), 2) if calories_list else 0
    total_interactions=len(saved_dishes) +len(recommendations)

    # summary_obj = HabitSummary(
    #     headline="Your Eating Habits Overview",
    #     insights=f"Avg calories per meal: {avg_calories} kcal. Total interactions: {total_interactions}.",
    #     weekly_trends={"avg_calories": avg_calories},
    #     most_liked_tags=sorted(liked_tags, key=liked_tags.get, reverse=True)[:5],
    #     most_disliked_tags=sorted(disliked_tags, key=disliked_tags.get, reverse=True)[:5],
    #     recommended_cuisines=list(cuisines),
    #     total_interactions=total_interactions
    #     )
    structured = {
        "headline": "Your Eating Habits Overview",
        "insights": f"Avg calories per meal: {avg_calories} kcal. Total interactions: {total_interactions}.",
        "weekly_trends": {"avg_calories": avg_calories},
        "tags": {
            "liked": sorted(liked_tags, key=liked_tags.get, reverse=True)[:5],
            "disliked": sorted(disliked_tags, key=disliked_tags.get, reverse=True)[:5]
        },
        "recommended_cuisines": list(cuisines),
        "totals": {
            "interactions": total_interactions,
            "avg_calories": avg_calories
        }
    }
    
    


    prompt=f"""
You are a habit Tracker AI. Given the structured user summary below,generate exactly 4 short bullet points(max 12 words each)
desscribing user's eating patterns.

Return ONLY valid JSON using this schema:
{{
"summary_points":["...","...","...","..."]
}}
User Summary:
{json.dumps(structured)} 
Detect Patterns:
{json.dumps(state.get("patterns",{}))}
"""
    llm_response=llm.invoke(prompt)

    output_text=getattr(llm_response,"content","{}")
    try:
        ai_json=json.loads(output_text)
    except:
        ai_json={"summary_points":["Unable to parse LLM Output"]}
    
    structured["ai_summary"]=ai_json
    return {**state,"habit_summary":structured}

#     clean_output = {
#     "headline": summary_obj.headline,
#     "insights": summary_obj.insights,
#     "weekly_trends": summary_obj.weekly_trends,
#     "tags": {
#         "liked": summary_obj.most_liked_tags,
#         "disliked": summary_obj.most_disliked_tags
#     },
#     "recommended_cuisines": summary_obj.recommended_cuisines,
#     "totals": {
#         "interactions": summary_obj.total_interactions,
#         "avg_calories": summary_obj.weekly_trends["avg_calories"]
#     },
#     "ai_summary": {
#         "points": llm_json.get("summary_points", [])
#     }
# }
    


def save_state(uid: str, state: dict):
    """Save habit agent state into Firestore."""
    try:
        db.collection("habit_states").document(uid).set(state)
        print(f"[HABIT] Saved state for {uid}")
    except Exception as e:
        print(f"[HABIT] Failed to save state: {e}")

def load_state(uid: str) -> dict:
    """Load habit agent state from Firestore."""
    try:
        doc = db.collection("habit_states").document(uid).get()
        if doc.exists:
            print(f"[HABIT] Loaded state for {uid}")
            return doc.to_dict()
        return None
    except Exception as e:
        print(f"[HABIT] Failed to load state: {e}")
        return None



graph=StateGraph(HabitState)

graph.add_node("fetch_dish_history",fetch_dish_history)
graph.add_node("fetch_dish_recommendations",fetch_dish_recommendations)
graph.add_node("fetch_analytics",fetch_analytics)
graph.add_node("generate_habit_summary",generate_habit_summary)
graph.add_node("extract_patterns",extract_patterns)

graph.add_edge(START,"fetch_dish_history")
graph.add_edge("fetch_dish_history","fetch_dish_recommendations")
graph.add_edge("fetch_dish_recommendations","fetch_analytics")
graph.add_edge("fetch_analytics","extract_patterns")
graph.add_edge("extract_patterns","generate_habit_summary")
graph.add_edge("generate_habit_summary",END)



habit_agent=graph.compile()
