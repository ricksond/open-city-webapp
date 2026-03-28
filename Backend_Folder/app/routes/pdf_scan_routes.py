# import os
# import json
# from flask import Blueprint, request, jsonify, g
# from werkzeug.utils import secure_filename

# # LangChain & Gemini Imports
# from langchain_google_genai import ChatGoogleGenerativeAI
# from langchain_huggingface import HuggingFaceEmbeddings
# from langchain_pinecone import PineconeVectorStore

# # Local Imports
# from app.pdf_scan_agent.utils import initialize_vector_store, build_workflow , PINECONE_INDEX_NAME
# from app.pdf_scan_agent.pdf_scan import build_workflow

# # Define the Blueprint
# pdf_bot_bp = Blueprint('pdf_bot', __name__)

# # --- GLOBAL INITIALIZATION ---
# # These are initialized once when the module is imported
# initialize_vector_store()
# embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
# vector_store = PineconeVectorStore(index_name=PINECONE_INDEX_NAME, embedding=embeddings)
# llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
# rag_application = build_workflow(vector_store, llm)

# # --- ROUTES ---

# @pdf_bot_bp.route("/upload", methods=["POST"])
# def upload_pdf():
#     """Endpoint for Node.js to send PDF files for indexing."""
#     if 'file' not in request.files:
#         return jsonify({"error": "No file part"}), 400

#     file = request.files['file']
#     if file.filename == '' or not file.filename.endswith('.pdf'):
#         return jsonify({"error": "Invalid file. Only PDFs allowed."}), 400

#     # Save temporarily to process
#     filename = secure_filename(file.filename)
#     temp_path = os.path.join("/tmp", f"temp_{filename}")
#     file.save(temp_path)

#     try:
#         # Index the PDF into Pinecone
#         build_workflow(temp_path, vector_store)
#         return jsonify({"message": f"Successfully indexed {filename}"}), 201
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500
#     finally:
#         if os.path.exists(temp_path):
#             os.remove(temp_path)

# @pdf_bot_bp.route("/ask", methods=["POST"])
# def ask_question():
#     """Endpoint for Node.js to send user questions."""
#     data = request.get_json()

#     if not data or 'question' not in data:
#         return jsonify({"error": "Missing 'question' in request body"}), 400

#     try:
#         # Run the LangGraph workflow
#         result = rag_application.invoke({"question": data['question']})
#         return jsonify({"answer": result["answer"]}), 200
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500

# @pdf_bot_bp.route("/health", methods=["GET"])
# def health_check():
#     return jsonify({"status": "online"}), 200


from flask import request, jsonify
from dotenv import load_dotenv
from app.pdf_scan_agent.pdf_scan import (
    initialize_vector_store,
    build_workflow,
    process_and_embed_pdf
)
from langchain_google_genai import ChatGoogleGenerativeAI
import os
from flask import Blueprint, request, jsonify
from werkzeug.utils import secure_filename
from datetime import datetime

# Firebase Imports
from .. import firebase
from firebase_admin import firestore
db = firebase.db

# LangChain & Gemini Imports

# Local Imports

load_dotenv()

# Define the Blueprint
pdf_bot_bp = Blueprint('pdf_bot', __name__, url_prefix="/pdf_bot")

# --- GLOBAL INITIALIZATION ---
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

# --- FIXED EXTRACTION CATEGORIES ---
# EXTRACTION_QUERIES = {
#     "budget": "What is the total budget, cost, financial amount, or funding mentioned?",
#     "insurance": "What are the insurance requirements, liability coverage, or policies?",
#     "contract_start_date": "What is the contract start date, effective date, or commencement date?",
#     "contract_end_date": "What is the contract end date, expiration date, or completion date?"
# }
EXTRACTION_QUERIES = {
    "correctness":
        "Are there any logical errors, incorrect assumptions, or edge cases that may cause incorrect behavior? ",
    "best_practices":
        "Does the code follow language/framework-specific best practices? "
}

# --- ROUTES ---


@pdf_bot_bp.route("/process-local", methods=["POST"])
def process_local_pdf():
    # 1. FIX THE 415 ERROR: use force=True to ignore missing Content-Type headers
    data = request.get_json(force=True)

    # 2. Extract the path from the JSON key "file_path"
    # Expected JSON: {"file_path": "C:\\Users\\ADMIN\\Desktop\\...\\3643773.pdf"}
    local_path = data.get('file_path')

    if not local_path:
        return jsonify({"error": "Missing 'file_path' in request body"}), 400

    # 3. Clean the path (handles potential double-slashes or backslashes from Windows)
    local_path = os.path.normpath(local_path)

    # 4. Safety check: Ensure the file actually exists
    if not os.path.exists(local_path):
        return jsonify({"error": f"File not found at: {local_path}"}), 404

    if not local_path.lower().endswith('.pdf'):
        return jsonify({"error": "The specified file is not a PDF."}), 400

    filename = os.path.basename(local_path)

    try:
        # 5. Process and Embed
        process_and_embed_pdf(local_path, vector_store)

        # 6. Extract fixed categories
        extracted_data = {}
        for category, query in EXTRACTION_QUERIES.items():
            result = rag_application.invoke({"question": query})
            extracted_data[category] = result["answer"].strip()

        # 7. Prepare payload for Firebase
        document_payload = {
            "filename": filename,
            "local_source_path": local_path,
            "processed_at": datetime.utcnow().isoformat(),
            "extracted_data": extracted_data
        }

        # 8. Save to Firestore
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
    """Reads PDF -> Chunks -> Embeds in Pinecone -> Extracts fixed categories -> Saves to Firebase"""

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.pdf'):
        return jsonify({"error": "Invalid file. Only PDFs allowed."}), 400

    filename = secure_filename(file.filename)
    temp_path = os.path.join("/tmp", f"temp_{filename}")
    file.save(temp_path)

    try:
        # 1. Chunk and Embed the PDF into Pinecone
        process_and_embed_pdf(temp_path, vector_store)

        # 2. Extract fixed categories
        extracted_data = {}
        for category, query in EXTRACTION_QUERIES.items():
            result = rag_application.invoke({"question": query})
            extracted_data[category] = result["answer"].strip()

        # 3. Prepare payload for Firebase
        document_payload = {
            "filename": filename,
            "processed_at": datetime.utcnow().isoformat(),
            "extracted_data": extracted_data
        }

        # 4. Save to Firestore
        # Creates or updates a document in 'pdf_extractions' collection using the filename as the document ID
        doc_ref = db.collection('pdf_extractions').document(filename)
        doc_ref.set(document_payload)

        # 5. Return JSON response to the client
        return jsonify({
            "message": f"Successfully processed {filename}",
            "data": document_payload
        }), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Cleanup temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@pdf_bot_bp.route("/health", methods=["GET"])
def health_check():
    return jsonify({"status": "online"}), 200
