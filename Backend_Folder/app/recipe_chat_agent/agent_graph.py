import json
from typing import TypedDict, List, Optional
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END

from .utils import get_llm
from .. import firebase 
from firebase_admin import firestore
db = firebase.db

llm = get_llm()


class Recipe(BaseModel):
    title: str
    ingredients: List[str]
    steps: List[str]
    metadata: dict = Field(default_factory=lambda: {
        "prep_time": "N/A",
        "cook_time": "N/A",
        "servings": 2
    })

class RecipeState(TypedDict):
    user_message: Optional[str]
    recipe_request: Optional[str]
    missing_ingredients: List[str]
    current_recipe: Optional[Recipe]
    current_step_index: int
    bot_response: str
    history: List[dict]


def load_state(uid: str) -> Optional[RecipeState]:
    doc = db.collection("recipe_states").document(uid).get()
    if doc.exists:
        state = doc.to_dict()
        if state.get("current_recipe"):
            state["current_recipe"] = Recipe(**state["current_recipe"])
        return state
    return None


def generate_recipe(state: RecipeState, config) -> RecipeState:
    request = state.get("recipe_request") or ""

    prompt_text = f"""
    Generate a simple, realistic recipe for {request} and estimate basic nutritional information per serving.
    Respond ONLY with valid JSON matching this exact schema, with approximate numeric values (e.g., "220 kcal", "15 g"):

    {{
        "name": "Name of the recipe",
        "ingredients": ["Ingredient 1", "Ingredient 2"],
        "steps": ["Step 1 text...", "Step 2 text..."],
        "metadata": {{
            "prep_time": "10 min",
            "cook_time": "20 min",
            "servings": 1,
            "calories": "220 kcal",
            "protein": "25 g",
            "carbs": "5 g",
            "fat": "10 g"
        }},
        "image_url": null
    }}
    Make sure all fields are filled in realistically and in the correct format.
    """

    raw = llm.invoke(prompt_text).content.strip()

    try:
        json_start = raw.find('{')
        json_end = raw.rfind('}') + 1
        if json_start == -1 or json_end == 0:
            raise json.JSONDecodeError("No JSON object found in LLM response.", raw, 0)
        json_str = raw[json_start:json_end]
        recipe_dict = json.loads(json_str)
        recipe_dict.setdefault("image_url", None)
        recipe_dict.setdefault(
            "metadata",
            {
                "prep_time": "N/A",
                "cook_time": "N/A",
                "servings": 2,
                "calories": "N/A",
                "protein": "N/A",
                "carbs": "N/A",
                "fat": "N/A",
            },
        )
        for key in ["calories", "protein", "carbs", "fat"]:
            if key not in recipe_dict["metadata"]:
                recipe_dict["metadata"][key] = "N/A"

        recipe_dict["name_lowercase"] = recipe_dict["name"].lower()
        recipe_dict["created_by"] = "bot"
        recipe_dict["created_at"] = firestore.SERVER_TIMESTAMP
        dish_doc_ref = db.collection("dishes").document()
        dish_doc_ref.set(recipe_dict)
        recipe_id = dish_doc_ref.id
        uid = config["configurable"].get("thread_id")
        if uid:
            user_history_ref = (
                db.collection("userRecipes")
                .document(uid)
                .collection("saved")
                .document(recipe_id)
            )
            user_history_ref.set({
                "recipe_id": recipe_id,
                "saved_at": firestore.SERVER_TIMESTAMP,
                "saved_by": uid
            })
        recipe_for_state = Recipe(
            title=recipe_dict["name"],
            ingredients=recipe_dict["ingredients"],
            steps=recipe_dict["steps"],
            metadata=recipe_dict["metadata"]
        )
        nutrition_info = recipe_dict["metadata"]
        reply_message = (
            f"Recipe loaded: {recipe_for_state.title}\n"
            f"Calories: {nutrition_info.get('calories', 'N/A')}, "
            f"Protein: {nutrition_info.get('protein', 'N/A')}, "
            f"Carbs: {nutrition_info.get('carbs', 'N/A')}, "
            f"Fat: {nutrition_info.get('fat', 'N/A')}"
        )

        new_state = {
            **state,
            "current_recipe": recipe_for_state,
            "current_step_index": -1,
            "missing_ingredients": [],
            "user_message": None,
            "bot_response": json.dumps({"reply": reply_message}),
            "history": state.get("history", []) + [
                {"recipe_id": recipe_id, "title": recipe_for_state.title}
            ],
        }

        return new_state

    except json.JSONDecodeError:
        return {
            **state,
            "bot_response": json.dumps({
                "reply": "I had trouble generating that recipe. Could you try rephrasing your request?"
            })
        }

    except Exception as e:
        print(f"[NODE] Failed to parse or save dish: {e}")
        return {
            **state,
            "bot_response": json.dumps({
                "reply": "Failed to parse or save recipe JSON."
            })
        }



def provide_next_step(state: RecipeState) -> RecipeState:
    recipe = state.get("current_recipe")
    if not recipe:
        reply = {"reply": "No recipe loaded."}
        return {**state, "bot_response": json.dumps(reply)}
    idx = state["current_step_index"]
    if idx >= len(recipe.steps) - 1:
        reply = {"reply": "You're done! Enjoy your meal!"}
        return {**state, "current_step_index": len(recipe.steps), "bot_response": json.dumps(reply)}
    next_idx = idx + 1
    step_text = recipe.steps[next_idx]
    prompt_text = f'Next step: "{step_text}" Respond only with JSON: {{"reply":"..."}}'
    raw = llm.invoke(prompt_text).content.strip()
    if raw.startswith("```json"):
        raw = raw.strip("```json\n").strip("```")
    return {**state, "current_step_index": next_idx, "bot_response": raw}

def repeat_step(state: RecipeState) -> RecipeState:
    recipe = state.get("current_recipe")
    idx = state.get("current_step_index", -1)
    if not recipe:
        reply = "No recipe loaded."
    elif idx == -1:
        reply = "Ingredients:\n" + "\n".join(f"- {i}" for i in recipe.ingredients)
    elif idx < len(recipe.steps):
        reply = f"Step {idx+1}: {recipe.steps[idx]}"
    else:
        reply = "You already finished!"
    return {**state, "bot_response": json.dumps({"reply": reply})}

def handle_missing_ingredient(state: RecipeState) -> RecipeState:
    recipe = state.get("current_recipe")
    user_msg = state.get("user_message") or ""
    if not recipe:
        reply = "No recipe loaded."
    else:
        prompt_text = f'User said "{user_msg}". Suggest a substitute for missing ingredient. Respond only JSON: {{"reply":"..."}}'
        raw = llm.invoke(prompt_text).content.strip()
        if raw.startswith("```json"):
            raw = raw.strip("```json\n").strip("```")
        try:
            reply = json.loads(raw).get("reply", "Could not suggest a substitute.")
        except:
            reply = "Could not suggest a substitute."
    return {**state, "bot_response": json.dumps({"reply": reply})}

def answer_question(state: RecipeState) -> RecipeState:
    q = state.get("user_message", "")
    recipe = state.get("current_recipe")
    idx = state.get("current_step_index", -1)
    if not recipe:
        reply = "No recipe loaded."
    else:
        ctx = {"title": recipe.title, "step_index": idx, "step": recipe.steps[idx] if 0 <= idx < len(recipe.steps) else None}
        prompt_text = f'User asks: "{q}". Context: {json.dumps(ctx)}. Respond only JSON: {{"reply":"..."}}'
        raw = llm.invoke(prompt_text).content.strip()
        if raw.startswith("```json"):
            raw = raw.strip("```json\n").strip("```")
        try:
            reply = json.loads(raw).get("reply", "Couldn't answer.")
        except:
            reply = "Couldn't answer."
    return {**state, "bot_response": json.dumps({"reply": reply})}

def handle_fallback(state: RecipeState) -> RecipeState:
    return {**state, "bot_response": json.dumps({"reply": "I didn't understand that."})}


def llm_router(state: RecipeState,config) -> str:
    if state.get("recipe_request") and not state.get("current_recipe"):
        return "generate_recipe"
    if not state.get("current_recipe"):
        return "handle_fallback"
    router_input = {
        "user_message": state.get("user_message"),
        "missing_ingredients": state.get("missing_ingredients"),
        "current_step_index": state.get("current_step_index"),
        "has_recipe": bool(state.get("current_recipe"))
    }
    prompt_text = f"""
    Decide one action. Actions: generate_recipe, provide_next_step, repeat_step, handle_missing_ingredient, answer_question, handle_fallback.
    Respond JSON: {{"action":"..."}}
    Current state: {json.dumps(router_input)}
    """
    raw = llm.invoke(prompt_text).content.strip()
    if raw.startswith("```json"):
        raw = raw.strip("```json\n").strip("```")
    try:
        action = json.loads(raw).get("action", "handle_fallback")
    except:
        action = "handle_fallback"
    valid = {"generate_recipe","provide_next_step","repeat_step","handle_missing_ingredient","answer_question","handle_fallback"}
    if action not in valid:
        action = "handle_fallback"
    print(f"   -> Router LLM chose action: {action}")
    return action


def build_graph():
    g = StateGraph(RecipeState)
    g.add_node("generate_recipe", generate_recipe)
    g.add_node("provide_next_step", provide_next_step)
    g.add_node("repeat_step", repeat_step)
    g.add_node("handle_missing_ingredient", handle_missing_ingredient)
    g.add_node("answer_question", answer_question)
    g.add_node("handle_fallback", handle_fallback)
    g.add_node("llm_router", llm_router)
    g.add_conditional_edges(START, llm_router, {
        "generate_recipe":"generate_recipe",
        "provide_next_step":"provide_next_step",
        "repeat_step":"repeat_step",
        "handle_missing_ingredient":"handle_missing_ingredient",
        "answer_question":"answer_question",
        "handle_fallback":"handle_fallback"
    })
    for n in ["generate_recipe","provide_next_step","repeat_step","handle_missing_ingredient","answer_question","handle_fallback"]:
        g.add_edge(n, END)
    g.add_conditional_edges("llm_router", llm_router, {
        "generate_recipe":"generate_recipe",
        "provide_next_step":"provide_next_step",
        "repeat_step":"repeat_step",
        "handle_missing_ingredient":"handle_missing_ingredient",
        "answer_question":"answer_question",
        "handle_fallback":"handle_fallback"
    })
    return g.compile()


recipe_app = build_graph()
