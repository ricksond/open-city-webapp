import json
from flask import Blueprint,request,jsonify,g
from functools import wraps
from app.habit_tracking_agent.agent4 import habit_agent,load_state, save_state
from .. import firebase

db=firebase.db
habit=Blueprint("habit_tracking",__name__,url_prefix="/habit_tracking")

def require_auth(f):
    @wraps(f)
    def wrapper(*args,**kwargs):
        auth_header=request.headers.get("Authorization","")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error":" Missing or invalid Token"}),401
        
        g.uid=auth_header.split(" ",1)[1]
        return f(*args,**kwargs)
    return wrapper

@habit.route("/start",methods=["POST"])
@require_auth
def start_habit_tracking():
    """ Habit Analysis Starter """

    try:
        user_doc=db.collection("users").document(g.uid).get()
        if user_doc.exists:
            user_data=user_doc.to_dict()
            dish_history=user_data.get("dish_history",[])
            preferences=user_data.get("user_preferences",{})
        else:
            dish_history=[]
            preferences={}
        
        state={
            "uid":g.uid,
            "saved_dishes":dish_history,
            "recommendations":[],
            "analytics":{},
            "habit_summary":None
        }
    except Exception as e:
        print(f"Error Loading User doc {g.uid}:{e}")
        return jsonify({"error":"Failed to load user Data"}),500

    config={"configurable":{"thread_id":g.uid}}
    final_state=habit_agent.invoke(state,config=config)
    save_state(g.uid,final_state)
    return jsonify({"summary":final_state.get("habit_summary")})

@habit.route("/update",methods=['POST'])
@require_auth
def update_habit_tracking():
    """
    Updates Habit whenever the user tries something new
    
    """
    data=request.json or {}
    user_message=data.get("message","")
    old_state=load_state(g.uid)
    if not old_state:
        print(f"No Habits found for {g.uid},starting new tracking session.")
        return start_habit_tracking()
    new_state={
        **old_state,
        "user_message":user_message,
        "uid":g.uid
    }
    config={"configurable":{"thread_id":g.uid}}
    final_state=habit_agent.invoke(new_state,config=config)
    save_state(g.uid,final_state)

    
    return jsonify({"summary":final_state.get("habit_summary")})