
import os
import json
from datetime import datetime
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

from app.pdf_scan_agent.pdf_scan import (
    initialize_vector_store,
    build_workflow,
    process_and_embed_pdf
)
from langchain_google_genai import ChatGoogleGenerativeAI
from .. import firebase

db = firebase.db
load_dotenv()

pdf_bot_bp = Blueprint('pdf_bot', __name__, url_prefix="/pdf_bot")

PINECONE_INDEX_NAME = "pdf-scan-bot-index"
GOOGLE_KEY = os.getenv("GOOGLE_API_KEY")
PINECONE_KEY = os.getenv("PINECONE_API_KEY")

vector_store = initialize_vector_store(
    pinecone_key=PINECONE_KEY,
    google_key=GOOGLE_KEY,
    index_name=PINECONE_INDEX_NAME
)

llm = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=0,
    google_api_key=GOOGLE_KEY
)
rag_application = build_workflow(vector_store, llm)

def parse_llm_json(response_text: str) -> dict:
    text = response_text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        return {"raw_output": response_text}

@pdf_bot_bp.route("/process-local", methods=["POST"])
def process_local_pdf():
    data = request.get_json(force=True)
    local_path = data.get('file_path')
    
    if not local_path:
        return jsonify({"error": "Missing 'file_path' in request body"}), 400
        
    local_path = os.path.normpath(local_path)
    if not os.path.exists(local_path):
        return jsonify({"error": f"File not found at: {local_path}"}), 404
        
    if not local_path.lower().endswith('.pdf'):
        return jsonify({"error": "The specified file is not a PDF."}), 400
        
    filename = os.path.basename(local_path)
    
    try:
        process_and_embed_pdf(local_path, vector_store)
        
        result = rag_application.invoke({"question": "Extract procurement data"})
        extracted_data = parse_llm_json(result["answer"])
        
        document_payload = {
            "filename": filename,
            "local_source_path": local_path,
            "processed_at": datetime.utcnow().isoformat(),
            "extracted_data": extracted_data
        }
        
        doc_ref = db.collection('pdf_extractions').document(filename)
        doc_ref.set(document_payload)
        
        return jsonify({
            "message": f"Successfully processed local file: {filename}",
            "data": document_payload
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@pdf_bot_bp.route("/process", methods=["POST"])
def process_and_extract_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Invalid file. Only PDFs allowed."}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join("/tmp", f"temp_{filename}")
    file.save(temp_path)
    
    try:
        process_and_embed_pdf(temp_path, vector_store)
        
        result = rag_application.invoke({"question": "Extract procurement data"})
        extracted_data = parse_llm_json(result["answer"])
        
        document_payload = {
            "filename": filename,
            "processed_at": datetime.utcnow().isoformat(),
            "extracted_data": extracted_data
        }
        
        doc_ref = db.collection('pdf_extractions').document(filename)
        doc_ref.set(document_payload)
        
        return jsonify({
            "message": f"Successfully processed {filename}",
            "data": document_payload
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
        
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pdf_bot_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "online"}), 200