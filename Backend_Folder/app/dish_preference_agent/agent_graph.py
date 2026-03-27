import json
import re
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from .utils import get_llm
from .. import firebase
import random

db = firebase.db
llm = get_llm()
_compressed_uids = set()

def ensure_pref_shape(prefs):
    """Ensure preference dict has correct structure."""
    if not isinstance(prefs, dict):
        prefs = {}

    prefs.setdefault("liked_tags", {})
    prefs.setdefault("disliked_tags", {})
    return prefs


def _extract_text_from_llm_response(resp) -> str:
    """
    Try to extract a text/string from common LLM response shapes.
    Handles: str, bytes, dicts (openai-like), objects with .content/.text, etc.
    """
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
                if "message" in choice and isinstance(choice["message"], dict):
                    m = choice["message"]
                    if "content" in m and isinstance(m["content"], str):
                        return m["content"]
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
            if hasattr(choice0, "text"):
                return choice0.text
        except Exception:
            pass


    try:
        return str(resp)
    except Exception:
        return ""


def _strip_code_fences(s: str) -> str:
    """Remove ```...``` fences and leading/trailing whitespace."""
    s = re.sub(r"^```(?:json)?\s*", "", s, flags=re.IGNORECASE)
    s = re.sub(r"\s*```$", "", s)
    return s.strip()


def _find_first_json_object(s: str) -> Optional[str]:
    """
    Try to find the first top-level JSON object substring in s.
    This uses a regex that is reasonably robust for nested braces.
    """
    pattern = re.compile(r"\{(?:[^{}]++|\{(?:[^{}]++|\{[^{}]*\})*\})*\}", flags=re.DOTALL)
    m = pattern.search(s)
    return m.group(0) if m else None


def compress_preferences_with_llm(prefs: dict, uid: Optional[str] = None) -> dict:
    """
    Uses LLM to compress liked/disliked tags if they exceed 10 items.
    Output retains structure:
    {
        "liked_tags": {"tag": strength},
        "disliked_tags": {"tag": strength}
    }

    This function is robust to different LLM response object shapes.
    It also guards against double-invoking the LLM for the same uid
    inside a single process (using _compressed_uids).
    """
    if uid is not None and uid in _compressed_uids:
        return prefs
    prompt = f"""
You are a system that compresses food preference tags.

Current preferences:
- liked_tags: {prefs.get("liked_tags", {})}
- disliked_tags: {prefs.get("disliked_tags", {})}

Task:
- Reduce each to the top 4–5 most meaningful tags.
- Keep strength (frequency) values as integers.
- The JSON structure MUST remain:

{{
    "liked_tags": {{"tag": strength}},
    "disliked_tags": {{"tag": strength}}
}}

Return ONLY valid JSON. No explanation.
"""

    try:
        raw_resp = llm.invoke(prompt)
        if uid is not None:
            _compressed_uids.add(uid)

        text = _extract_text_from_llm_response(raw_resp)
        if not text:
            raise ValueError("Empty text extracted from LLM response")
        text = _strip_code_fences(text)
        try:
            parsed = json.loads(text)
            return ensure_pref_shape(parsed)
        except Exception:
            json_sub = _find_first_json_object(text)
            if json_sub:
                try:
                    parsed = json.loads(json_sub)
                    return ensure_pref_shape(parsed)
                except Exception as e_sub:
                    print("LLM compression: failed to parse JSON substring:", e_sub)
        print("LLM compression: couldn't parse response, returning original prefs")
        return prefs

    except Exception as e:
        print("LLM compression error:", e)
        if uid is not None and uid in _compressed_uids:
            _compressed_uids.discard(uid)
        return prefs

class Dish(BaseModel):
    name: str
    tags: List[str] = Field(default_factory=list)
    image_url: Optional[str] = None
    metadata: dict = Field(default_factory=lambda: {
        "cuisine": "Unknown",
        "difficulty": "N/A",
        "rating": 0
    })


class DishState(TypedDict):
    uid: Optional[str]
    user_message: Optional[str]
    current_dish: Optional[Dish]
    preference_action: Optional[str]
    user_preferences: dict
    bot_response: str
    history: List[dict]


def save_state(uid: str, state: DishState):
    state_to_save = state.copy()
    if "user_preferences" in state_to_save:
        state_to_save["user_preferences"] = ensure_pref_shape(
            state_to_save["user_preferences"]
        )
    if state_to_save.get("current_dish"):
        state_to_save["current_dish"] = state_to_save["current_dish"].dict()

    db.collection("dish_states").document(uid).set(state_to_save)


def load_state(uid: str) -> Optional[DishState]:
    doc = db.collection("dish_states").document(uid).get()
    if not doc.exists:
        return None
    state = doc.to_dict()
    state["user_preferences"] = ensure_pref_shape(
        state.get("user_preferences", {})
    )
    if state.get("current_dish"):
        state["current_dish"] = Dish(**state["current_dish"])
    return state


def get_next_dish(uid: str) -> Optional[Dish]:
    docs = list(db.collection("dishes").stream())
    if not docs:
        return None
    return Dish(**random.choice(docs).to_dict())



def update_user_preference(uid: str, dish: Dish, action: str):
    ref = db.collection("users").document(uid)

    try:
        doc = ref.get()
        prefs = ensure_pref_shape(doc.to_dict().get("user_preferences", {})) if doc.exists else ensure_pref_shape({})
    except:
        prefs = ensure_pref_shape({})
    for tag in dish.tags:
        if action == "like":
            prefs["liked_tags"][tag] = prefs["liked_tags"].get(tag, 0) + 1
        else:
            prefs["disliked_tags"][tag] = prefs["disliked_tags"].get(tag, 0) + 1
    if len(prefs["liked_tags"]) > 10 or len(prefs["disliked_tags"]) > 10:
        prefs = compress_preferences_with_llm(prefs, uid=uid)

    ref.update({"user_preferences": prefs})
    return prefs


def present_dish(state: DishState) -> DishState:
    dish = get_next_dish(state.get("uid"))
    if not dish:
        return {**state, "bot_response": json.dumps({"reply": "No dishes found!"})}

    reply = {
        "reply": f"Would you like to try '{dish.name}'? Tags: {', '.join(dish.tags)}",
        "dish": dish.dict(),
    }

    return {**state, "current_dish": dish, "bot_response": json.dumps(reply)}


def handle_preference(state: DishState) -> DishState:
    uid = state.get("uid")
    msg = (state.get("user_message") or "").lower()
    action = state.get("preference_action")
    if not action:
        if msg in ["like", "yes", "love it"]:
            action = "like"
        elif msg in ["dislike", "no", "nah"]:
            action = "dislike"

    dish = state.get("current_dish")

    if not dish or action not in ["like", "dislike"]:
        return {**state, "bot_response": json.dumps({"reply": "Say like/dislike."})}
    updated_prefs = update_user_preference(uid, dish, action)
    next_dish = get_next_dish(uid)

    if not next_dish:
        return {**state, "bot_response": json.dumps({"reply": "No more dishes!"})}

    reply = {
        "reply": f"You {action}d {dish.name}. Next: {next_dish.name}",
        "dish": next_dish.dict(),
        "preferences": updated_prefs
    }

    return {
        **state,
        "current_dish": next_dish,
        "user_preferences": updated_prefs,
        "bot_response": json.dumps(reply),
        "user_message": None
    }


def handle_fallback(state: DishState) -> DishState:
    return {**state, "bot_response": json.dumps({"reply": "Please say like/dislike."})}

def llm_router(state: DishState):
    if not state.get("current_dish"):
        return "present_dish"

    msg = (state.get("user_message") or "").lower()

    if msg in ["like", "yes", "love it"]:
        return "handle_preference"
    if msg in ["dislike", "no", "nah"]:
        return "handle_preference"

    return "handle_fallback"

def build_graph():
    graph = StateGraph(DishState)

    graph.add_node("present_dish", present_dish)
    graph.add_node("handle_preference", handle_preference)
    graph.add_node("handle_fallback", handle_fallback)

    graph.add_conditional_edges(START, llm_router, {
        "present_dish": "present_dish",
        "handle_preference": "handle_preference",
        "handle_fallback": "handle_fallback",
    })

    graph.add_edge("present_dish", END)
    graph.add_edge("handle_preference", END)
    graph.add_edge("handle_fallback", END)

    return graph.compile()


dish_agent = build_graph()
