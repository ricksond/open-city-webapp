import json
import re
from typing import TypedDict, Optional, List, Dict, Any
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from .utils import get_llm
from .. import firebase
import time

db = firebase.db
llm = get_llm()


def _extract_text_from_llm_response(resp: Any) -> str:
    """
    Extract a textual reply from common LLM response shapes.
    Handles: raw string, dict-like (choices/message/content), objects with .content/.text, etc.
    """
    if resp is None:
        return ""
    if isinstance(resp, str):
        return resp
    if isinstance(resp, bytes):
        return resp.decode("utf-8", errors="ignore")
    if isinstance(resp, dict):
        if "content" in resp and isinstance(resp["content"], str):
            return resp["content"]
        if "text" in resp and isinstance(resp["text"], str):
            return resp["text"]
        if "message" in resp:
            msg = resp["message"]
            if isinstance(msg, dict) and "content" in msg and isinstance(msg["content"], str):
                return msg["content"]
        if "choices" in resp and isinstance(resp["choices"], list) and resp["choices"]:
            choice = resp["choices"][0]
            if isinstance(choice, dict):
                if "text" in choice and isinstance(choice["text"], str):
                    return choice["text"]
                if "content" in choice and isinstance(choice["content"], str):
                    return choice["content"]
                if "message" in choice and isinstance(choice["message"], dict) and "content" in choice["message"]:
                    return choice["message"]["content"]
    if hasattr(resp, "content") and isinstance(getattr(resp, "content"), str):
        return getattr(resp, "content")
    if hasattr(resp, "text") and isinstance(getattr(resp, "text"), str):
        return getattr(resp, "text")
    if hasattr(resp, "choices") and getattr(resp, "choices"):
        try:
            choice0 = getattr(resp, "choices")[0]
            if isinstance(choice0, dict):
                if "text" in choice0 and isinstance(choice0["text"], str):
                    return choice0["text"]
                if "message" in choice0 and isinstance(choice0["message"], dict) and "content" in choice0["message"]:
                    return choice0["message"]["content"]
            if hasattr(choice0, "message") and hasattr(choice0.message, "content"):
                return choice0.message.content
        except Exception:
            pass
    try:
        return str(resp)
    except Exception:
        return ""


def _strip_code_fences(s: str) -> str:
    if not isinstance(s, str):
        return ""
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _find_first_json_substring(s: str) -> Optional[str]:
    if not isinstance(s, str):
        return None
    pattern = re.compile(r"\{(?:[^{}]++|\{(?:[^{}]++|\{[^{}]*\})*\})*\}|\[(?:[^\[\]]++|\[(?:[^\[\]]++|\[[^\[\]]*\])*\])*\]", flags=re.DOTALL)
    m = pattern.search(s)
    return m.group(0) if m else None


def safe_parse_json_from_text(text: str) -> Any:
    """
    Try best-effort to parse JSON from LLM text output.
    Returns dict/list on success, else None.
    """
    if not text:
        return None
    cleaned = _strip_code_fences(text)
    try:
        return json.loads(cleaned)
    except Exception:
        pass
    sub = _find_first_json_substring(cleaned)
    if sub:
        try:
            return json.loads(sub)
        except Exception:
            pass
    return None


def llm_invoke_text(prompt: str) -> str:
    """
    Invoke the llm and return a cleaned string result.
    Keeps things robust across SDK response shapes.
    """
    resp = llm.invoke(prompt)
    text = _extract_text_from_llm_response(resp) or ""
    return text.strip()

class Meal(BaseModel):
    name: str
    ingredients: Optional[List[str]] = None
    cooking_time: Optional[str] = None
    calories: Optional[str] = None


class Recommendation(BaseModel):
    title: str
    summary: str
    meal: Meal
    cuisine: Optional[str] = None
    diet: Optional[str] = None
    metadata: dict = Field(default_factory=lambda: {"confidence": 0.9, "source": "ai"})


class UserPreferences(TypedDict, total=False):
    liked_tags: Dict[str, int]
    disliked_tags: Dict[str, int]


class UserProfile(TypedDict, total=False):
    uid: Optional[str]
    cuisine: Optional[str]
    diet: Optional[str]
    preferredFood: Optional[str]
    user_preferences: Optional[UserPreferences]
    feedback: Optional[str]



class RecommendState(TypedDict, total=False):
    uid: Optional[str]
    retry_count: int
    user_profile: Optional[UserProfile]
    user_message: Optional[str]
    recommendation_request: Optional[str]
    current_recommendation: Optional[Recommendation]
    selected_meal: Optional[str]
    feedback: Optional[str]
    bot_response: str
    history: list
    route: Optional[str]


def save_state(uid: str, state: RecommendState):
    state_copy = dict(state)
    if state_copy.get("current_recommendation") and isinstance(state_copy["current_recommendation"], Recommendation):
        state_copy["current_recommendation"] = state_copy["current_recommendation"].dict()
    db.collection("recommendation_states").document(uid).set(state_copy)


def load_state(uid: str) -> RecommendState:
    doc_ref = db.collection("recommendation_states").document(uid)
    doc = doc_ref.get()
    if not doc.exists:
        return {"uid": uid, "retry_count": 0, "history": []}
    data = doc.to_dict() or {}
    if "current_recommendation" in data and isinstance(data["current_recommendation"], dict):
        try:
            data["current_recommendation"] = Recommendation(**data["current_recommendation"])
        except Exception:
            data["current_recommendation"] = None
    data.setdefault("retry_count", 0)
    data.setdefault("history", [])
    data.setdefault("uid", uid)
    return data

def safe_node_run(node_func, state: RecommendState) -> RecommendState:
    try:
        return node_func(state)
    except Exception as e:
        print(f"[NODE ERROR] {node_func.__name__}: {e}")
        state.setdefault("history", []).append({"error": str(e)})
        return {**state, "bot_response": json.dumps({"reply": "Internal server error."})}


def normalize_preferences(state: RecommendState) -> RecommendState:
    """
    Fixes conflicting tags before prompt creation.
    Rule: if a tag appears in both liked and disliked, treat it as DISLIKED.
    """
    profile = state.get("user_profile") or {}
    prefs = profile.get("user_preferences") or {}

    liked = prefs.get("liked_tags", {}) or {}
    disliked = prefs.get("disliked_tags", {}) or {}
    conflicts = set(liked.keys()) & set(disliked.keys())
    if conflicts:
        for tag in conflicts:
            liked.pop(tag, None)   
            disliked[tag] = 1      
        prefs["liked_tags"] = liked
        prefs["disliked_tags"] = disliked
        profile["user_preferences"] = prefs
        state["user_profile"] = profile

    return state

def build_recommendation_prompt(state: RecommendState) -> str:
    profile = state.get("user_profile") or {}
    prefs = profile.get("user_preferences") or {}
    liked = prefs.get("liked_tags", {})
    disliked = prefs.get("disliked_tags", {})
    cuisine = profile.get("cuisine", "unknown")
    diet = profile.get("diet", "unknown")
    preferred_food = profile.get("preferredFood", "none")
    time_of_day = prefs.get("recommendation_request_time", "unknown")
    feedback = state.get("feedback", "")
    if not feedback:
        pf = profile.get("feedback")
        if isinstance(pf, list) and pf:
            feedback = pf[-1]
        elif isinstance(pf, str):
            feedback = pf

    prompt_lines = [
        "You are a nutrition-aware meal recommendation assistant.",
        "You MUST generate exactly ONE realistic, healthy dish in JSON format.",
        "The recommendation must be fully personalized to the user.",
        "",
        "-------------------------------",
        "### PRIORITY ORDER FOR GENERATION",
        "1. NEWEST USER FEEDBACK → must be applied FIRST.",
        "2. Avoid recommending anything similar to the previous meal.",
        "3. Respect user preferences (liked/disliked tags).",
        "4. Respect user profile (cuisine, diet, preferred foods).",
        "5. Ensure the dish is healthy, realistic, and cookable.",
        "-------------------------------",
        "",
        "### CONFLICT RESOLUTION RULES (Strict)",
        "1. If the same tag appears in both Liked Tags and Disliked Tags, treat it as DISLIKED.",
        "2. Cuisine is a SOFT preference. If cuisine conflicts with *any* disliked tag or explicit feedback, DO NOT use that cuisine.",
        "3. Always prioritize: FEEDBACK > DISLIKED TAGS > DIET > LIKED TAGS > CUISINE.",
        "",
        "### User Profile",
        f"- Cuisine Preference: {cuisine}",
        f"- Diet Type: {diet}",
        f"- Preferred Food: {preferred_food}",
        f"- Time of Day: {time_of_day}",
        "",
        "### User Preferences",
        f"- Liked Tags (Prioritize): {list(liked.keys()) if liked else ['None']}",
        f"- Disliked Tags (Strictly Avoid): {list(disliked.keys()) if disliked else ['None']}",
    ]

    if feedback:
        prompt_lines.extend([
            "",
            "### Highest Priority: User Feedback",
            f'- Latest Feedback: "{feedback}"',
            "Apply this feedback directly when generating the new meal.",
        ])

    prompt_lines.extend([
        "",
        "-------------------------------",
        "### RECOMMENDATION RULES",
        "1. Recommend exactly ONE dish.",
        "2. Dish MUST respond to user feedback first.",
        "3. Dish MUST NOT conflict with disliked tags.",
        "4. Dish SHOULD prioritize liked tags.",
        "5. Dish SHOULD match diet strictly unless feedback overrides.",
        "6. Dish SHOULD match cuisine only when no conflicts exist.",
        "7. Keep calories realistic (350–750 kcal).",
        "8. Keep cooking times realistic (10–60 minutes).",
        "9. NO explanations, NO markdown, NO commentary outside JSON.",
        "",
        "Your output MUST be ONLY the JSON object below:",
        "",
        "```json",
        "{",
        '  "title": "Personalized Meal Recommendation",',
        '  "summary": "One-sentence explanation why this dish fits the user.",',
        '  "meal": {',
        '    "name": "Dish name",',
        '    "calories": "500",',
        '    "cooking_time": "25 minutes"',
        '  },',
        f'  "cuisine": "{cuisine}",',
        f'  "diet": "{diet}",',
        '  "metadata": {',
        '    "confidence": 0.90,',
        '    "source": "ai",',
        '    "applied_constraints": []',
        '  }',
        "}",
        "```",
    ])

    return "\n".join(prompt_lines)



def generate_recommendation(state: RecommendState) -> RecommendState:
    """
    Calls the LLM with the built prompt, parses JSON, builds Recommendation(),
    stores it in state["current_recommendation"], and returns updated state.
    """
    uid = state.get("uid")
    state.setdefault("retry_count", 0)
    state.setdefault("history", [])
    prompt = build_recommendation_prompt(state)
    raw_text = llm_invoke_text(prompt)
    parsed = safe_parse_json_from_text(raw_text)
    if not parsed or "meal" not in parsed:
        state["history"].append({
            "raw_llm": raw_text,
            "prompt": prompt,
            "ts": int(time.time()),
        })
        state["feedback"] = "Failed to parse recommendation JSON from LLM output."
        state["bot_response"] = json.dumps({
            "reply": "Failed to parse recommendation JSON."
        })
        return state
    meal_data = parsed.get("meal", {}) or {}
    calories_val = meal_data.get("calories")
    if calories_val is not None:
        calories_val = str(calories_val)
    meal = Meal(
        name=meal_data.get("name", ""),
        ingredients=meal_data.get("ingredients", []),
        cooking_time=meal_data.get("cooking_time"),
        calories=calories_val,  
    )
    rec = Recommendation(
        title=parsed.get("title", "Meal Recommendation"),
        summary=parsed.get("summary", ""),
        meal=meal,
        cuisine=parsed.get("cuisine"),
        diet=parsed.get("diet"),
        metadata=parsed.get("metadata", {"confidence": 0.9, "source": "ai"}),
    )
    updated_state = {
        **state,
        "current_recommendation": rec,
        "bot_response": json.dumps({"reply": "Meal recommendation ready."})
    }
    if uid:
        try:
            save_state(uid, updated_state)
        except Exception as e:
            print("[WARN] save_state failed:", e)

    return updated_state

def validate_recommendation(state: RecommendState) -> str:
    """
    Validates current recommendation stored in state.
    Returns "accept" or "regenerate". Also mutates state in-place:
      - increments retry_count when fails
      - sets state['feedback'] for next prompt
      - on 2nd failure auto-updates profile (cuisine/diet) in Firestore then accepts
    """
    print("[NODE] validate_recommendation")
    profile: UserProfile = state.get("user_profile") or {}
    rec: Optional[Recommendation] = state.get("current_recommendation")
    retry = state.get("retry_count", 0)
    state["retry_count"] = retry
    if not rec:
        print("[VALIDATE] No recommendation found.")
        state["feedback"] = "Failed to generate recommendation object."
        return "regenerate"
    disliked_tags = (profile.get("user_preferences") or {}).get("disliked_tags", {})
    expected_cuisine = profile.get("cuisine")
    expected_diet = profile.get("diet")
    validation_failed = False
    failure_reasons = []
    relax = retry >= 1
    if disliked_tags:
        meal_text = rec.meal.name.lower()
        if rec.meal.ingredients:
            meal_text += " " + " ".join([str(i).lower() for i in rec.meal.ingredients])
        for tag in disliked_tags.keys():
            if tag and tag.lower() in meal_text:
                validation_failed = True
                failure_reasons.append(f"Contains disliked tag: {tag}")
                break
    if expected_diet and rec.diet:
        if expected_diet.lower() not in rec.diet.lower():
            if not relax:
                validation_failed = True
                failure_reasons.append(f"Diet mismatch (Expected {expected_diet}, Got {rec.diet})")

    if validation_failed:
        retry += 1
        state["retry_count"] = retry
        if retry >= 2:
            print("[OVERRIDE] Repeated mismatch: overriding user profile with recommendation's values.")
            uid = state.get("uid")
            if expected_cuisine and rec.cuisine and expected_cuisine.lower() not in rec.cuisine.lower():
                profile["cuisine"] = rec.cuisine
            if expected_diet and rec.diet and expected_diet.lower() not in rec.diet.lower():
                profile["diet"] = rec.diet

            state["user_profile"] = profile
            state["feedback"] = None
            if uid:
                try:
                    db.collection("users").document(uid).set(profile, merge=True)
                    print(f"[OVERRIDE] Updated user profile saved for uid={uid}.")
                except Exception as e:
                    print("[OVERRIDE] Failed to save user profile:", e)
            return "accept"
        print(f"[VALIDATE] Failed attempt {retry}: {failure_reasons}")
        state["feedback"] = f"Previous attempt failed: {', '.join(failure_reasons)}. Please try a different dish."
        return "regenerate"
    state["retry_count"] = 0
    state["feedback"] = None
    return "accept"

def validate_node(state: RecommendState) -> RecommendState:
    route = validate_recommendation(state) 
    state["route"] = route
    return state


def validate_router(state: RecommendState) -> str:
    return state.get("route", "regenerate")

def build_graph():
    g = StateGraph(RecommendState)
    g.add_node("generate_recommendation", lambda s: safe_node_run(generate_recommendation, s))
    g.add_node("validate_node", lambda s: safe_node_run(validate_node, s))
    g.add_edge(START, "generate_recommendation")
    g.add_edge("generate_recommendation", "validate_node")
    g.add_conditional_edges(
        "validate_node",
        validate_router,
        {
            "accept": END,
            "regenerate": "generate_recommendation",
        }
    )
    return g.compile()

recommendation_agent = build_graph()
