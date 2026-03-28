import json
import os
from flask import Blueprint, jsonify, request
from datetime import datetime, timedelta
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage
from flask import jsonify, request
info_bp = Blueprint("info", __name__, url_prefix="/info")
load_dotenv()
def get_llm():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        print("Warning: GOOGLE_API_KEY not found in .env")
        return None
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash", 
        temperature=0.3,
        google_api_key=api_key
    )
def generate_summary(data, title):
    if not data:
        return "No data available."
    llm = get_llm()
    if not llm:
        return "AI Summary unavailable: API Key missing."

    prompt = f"""
    You are an expert procurement analyst. Analyze the following procurement data for {title}.
    Please provide:
    1. A brief executive summary of the spend and activity.
    2. Key insights (e.g., largest purchases, main entities/vendors involved).
    3. Top 3 highlights.
    Keep the tone professional, concise, and heavily data-driven.
    
    Data:
    {json.dumps(data, indent=2)[:15000]}
    """
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content
    except Exception as e:
        return f"Summary unavailable: {str(e)}"

vendors_dict = {}
entities_dict = {}
all_contracts = [] 

def check_expiry_soon(end_date_str):
    """Checks if a date is within the next 30 days."""
    if not end_date_str or end_date_str == "N/A":
        return False
    try:
        expiry_date = datetime.strptime(end_date_str, "%Y-%m-%d")
        today = datetime.now()
        thirty_days_from_now = today + timedelta(days=30)
        return today <= expiry_date <= thirty_days_from_now
    except ValueError:
        return False
    
def load_and_index_data():
    global vendors_dict, entities_dict, all_contracts
    current_dir = os.path.dirname(os.path.abspath(__file__))
    json_path = os.path.join(current_dir, "final_merged_data.json") 
    print(f"DEBUG: Looking for data at: {json_path}")
    try:
        with open(json_path, encoding="utf-8") as f:
            full_data = json.load(f)
        vendors = full_data.get("vendors", [])
        print(f"DEBUG: Successfully loaded {len(vendors)} vendors.")
    except Exception as e:
        print(f"ERROR: Loading failed: {e}")
        vendors = []
    new_vendors_dict = {}
    new_entities_dict = {}
    new_all_contracts = []
    for vendor in vendors:
        v_name = vendor.get("vendor_name", "Unknown Vendor").strip()
        v_id = vendor.get("vendor_id", "N/A")
        processed_contracts = []
        for contract in vendor.get("contracts", []):
            end_date = contract.get("effective_to", "N/A")
            contract_data = {
                "vendor_name": v_name,
                "contract_id": contract.get("contract_id") or contract.get("contract_number", "N/A"),
                "description": contract.get("description", "No description"),
                "start_date": contract.get("effective_from", "N/A"),
                "end_date": end_date,
                "amount": contract.get("amount", 0.0),
                "is_expiring_soon": check_expiry_soon(end_date)
            }
            processed_contracts.append(contract_data)
            new_all_contracts.append(contract_data)
        if v_name not in new_vendors_dict:
            new_vendors_dict[v_name] = {
                "vendor_id": v_id,
                "vendor_details": vendor.get("vendor_details", {}),
                "contracts": processed_contracts,
                "all_purchase_orders": [],
                "total_spend": 0.0,
                "entities_served": {} 
            }
        for po in vendor.get("purchase_orders", []):
            entity_info = po.get("entity", {})
            entity_name = entity_info.get("description", "Unknown Entity").strip()
            entity_code = entity_info.get("code", "N/A")
            po_total = 0.0
            items_bought = []
            for item in po.get("line_items", []):
                try:
                    item_total = float(item.get("line_total", 0.0))
                except (ValueError, TypeError):
                    item_total = 0.0
                po_total += item_total
                
                items_bought.append({
                    "po_number": po.get("order_number"),
                    "date": po.get("order_date"),
                    "item_description": item.get("item_description", "No description"),
                    "category": item.get("nigp_description", "Uncategorized"),
                    "quantity": item.get("quantity", 0),
                    "unit_price": item.get("unit_price", 0.0),
                    "total_cost": item_total
                })
            new_vendors_dict[v_name]["total_spend"] += po_total
            new_vendors_dict[v_name]["all_purchase_orders"].append(po)
            if entity_name not in new_vendors_dict[v_name]["entities_served"]:
                new_vendors_dict[v_name]["entities_served"][entity_name] = {"spend": 0.0, "po_count": 0}
            new_vendors_dict[v_name]["entities_served"][entity_name]["spend"] += po_total
            new_vendors_dict[v_name]["entities_served"][entity_name]["po_count"] += 1
            if entity_name not in new_entities_dict:
                new_entities_dict[entity_name] = {"entity_code": entity_code, "total_spend": 0.0, "vendors_used": {}}
            new_entities_dict[entity_name]["total_spend"] += po_total
            if v_name not in new_entities_dict[entity_name]["vendors_used"]:
                new_entities_dict[entity_name]["vendors_used"][v_name] = {"vendor_id": v_id, "total_spend_with_vendor": 0.0, "items_bought": []}
            new_entities_dict[entity_name]["vendors_used"][v_name]["total_spend_with_vendor"] += po_total
            new_entities_dict[entity_name]["vendors_used"][v_name]["items_bought"].extend(items_bought)
    vendors_dict = new_vendors_dict
    entities_dict = new_entities_dict
    all_contracts = new_all_contracts
    print(f"DEBUG: Indexing complete. {len(vendors_dict)} vendors, {len(all_contracts)} contracts.")
load_and_index_data()

@info_bp.route("/vendors", methods=["GET"])
def get_vendors():
    overview = {name: {"total_spend": round(v["total_spend"], 2), "id": v["vendor_id"]} for name, v in vendors_dict.items()}
    return jsonify(overview), 200

@info_bp.route("/entities", methods=["GET"])
def get_entities():
    overview = {name: {"total_spend": round(e["total_spend"], 2), "code": e["entity_code"]} for name, e in entities_dict.items()}
    return jsonify(overview), 200

@info_bp.route("/contracts", methods=["GET"])
def get_contracts():
    """Returns all contracts across all vendors."""
    return jsonify(all_contracts), 200

@info_bp.route("/contracts/expiring", methods=["GET"])
def get_expiring_contracts():
    """Returns only contracts expiring in the next 30 days."""
    expiring = [c for c in all_contracts if c["is_expiring_soon"]]
    return jsonify({
        "count": len(expiring),
        "contracts": expiring
    }), 200

@info_bp.route("/vendors/<vendor_name>", methods=["GET"])
def get_vendor_details(vendor_name):
    vendor = vendors_dict.get(vendor_name)
    if not vendor:
        normalized_name = vendor_name.lower().strip()
        match = next((v for v in vendors_dict if v.lower() == normalized_name), None)
        if match: vendor = vendors_dict[match]; vendor_name = match 
        else: return jsonify({"error": "Vendor not found"}), 404

    summary = generate_summary({"vendor": vendor_name, "total_spend": vendor["total_spend"], "contracts": vendor["contracts"]}, f"Vendor: {vendor_name}")
    return jsonify({
        "vendor_name": vendor_name,
        "total_spend": round(vendor["total_spend"], 2),
        "contracts": vendor["contracts"],
        "entities_served": vendor["entities_served"],
        "ai_summary": summary
    })
@info_bp.route("/dashboard/<name>", methods=["GET"])
def getDashInfo(name):
    normalized_name = name.lower().strip()
    vendor_match = next((v for v in vendors_dict if v.lower() == normalized_name), None)
    
    if vendor_match:
        vendor = vendors_dict[vendor_match]

        expiring_contracts = [c for c in vendor.get("contracts", []) if c.get("is_expiring_soon")]
        
        return jsonify({
            "type": "vendor",
            "name": vendor_match,
            "total_earnings": round(vendor.get("total_spend", 0), 2),
            "expiring_contracts_count": len(expiring_contracts),
            "entities_worked_with_count": len(vendor.get("entities_served", {}))
        }), 200
    entity_match = next((e for e in entities_dict if e.lower() == normalized_name), None)
    
    if entity_match:
        entity = entities_dict[entity_match]
        vendors_used = entity.get("vendors_used", {})
        sorted_vendors = sorted(
            vendors_used.items(), 
            key=lambda item: item[1].get("total_spend_with_vendor", 0), 
            reverse=True
        )[:3]
        
        top_3_details = []
        for v_name, v_data in sorted_vendors:
            vendor_profile = vendors_dict.get(v_name, {})
            expiring = [c for c in vendor_profile.get("contracts", []) if c.get("is_expiring_soon")]
            
            top_3_details.append({
                "vendor_name": v_name,
                "spend_with_entity": round(v_data.get("total_spend_with_vendor", 0), 2),
                "expiring_contracts": expiring
            })
            
        return jsonify({
            "type": "entity",
            "name": entity_match,
            "total_vendors_count": len(vendors_used),
            "top_3_vendors": top_3_details
        }), 200
    return jsonify({"error": "Record not found. Please check the vendor or entity name."}), 404
    
@info_bp.route("/entities/<entity_name>", methods=["GET"])
def get_entity_details(entity_name):
    entity = entities_dict.get(entity_name)
    if not entity:
        normalized_name = entity_name.lower().strip()
        match = next((e for e in entities_dict if e.lower() == normalized_name), None)
        if match: 
            entity = entities_dict[match]
            entity_name = match
        else: 
            return jsonify({"error": "Entity not found"}), 404
    try:
        summary = generate_summary(
            {"entity": entity_name, "total_spend": entity.get("total_spend", 0)}, 
            f"Entity: {entity_name}"
        )
    except Exception as e:
        print(f"AI Summary Error: {e}")
        summary = "Summary temporarily unavailable."
    all_vendors = entity.get("vendors_used", {})
    sorted_vendors = sorted(
        all_vendors.items(),
        key=lambda x: x[1].get("total_spend_with_vendor", 0),
        reverse=True
    ) 
    top_50_vendors = sorted_vendors[:50]
    trimmed_vendors = {}
    for v_name, v_data in top_50_vendors:
        items = v_data.get("items_bought", [])
        latest_items = sorted(items, key=lambda x: x.get("date", ""), reverse=True)[:3]
        
        trimmed_vendors[v_name] = {
            "total_spend_with_vendor": round(v_data.get("total_spend_with_vendor", 0), 2),
            "items_bought": latest_items
        }
    return jsonify({
        "entity_name": entity_name,
        "total_spend": round(entity.get("total_spend", 0), 2),
        "vendors_used": trimmed_vendors,
        "total_vendors_count": len(all_vendors),
        "ai_summary": summary
    })
@info_bp.route("/reload", methods=["POST"])
def reload_data():
    load_and_index_data()
    return jsonify({"status": "Data re-indexed"}), 200
