import time
import json
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

class GraphState(TypedDict):
    question: str
    context: List[Document]
    answer: str

def format_docs(docs: List[Document]) -> str:
    formatted_texts = []
    for doc in docs:
        page_num = doc.metadata.get('page', 'Unknown')
        formatted_texts.append(f"--- PAGE {page_num} ---\n{doc.page_content}")
    return "\n\n".join(formatted_texts)

def retrieve_node(state: GraphState, vector_store: PineconeVectorStore) -> dict:
    extraction_query = (
        "Contract number, Vendor name, Contract type, Maximum contract amount, "
        "Commencement date, Expiration date, Department, compliance clauses, "
        "what the city is buying, from whom, for how much, and for how long"
    )
    docs = vector_store.similarity_search(extraction_query, k=15)
    return {"context": docs}

def generate_node(state: GraphState, llm: ChatGoogleGenerativeAI) -> dict:
    formatted_context = format_docs(state["context"])
    prompt = PromptTemplate(
        template="""You are an automated procurement contract extractor.
        Extract the required information STRICTLY from the provided context. No external information.
        
        OUTPUT FORMAT: 
        You must return a valid, well-structured JSON object adhering to the schema below.
        For every extracted field, include the extracted "value", the exact verbatim "quote" from the text, and the "page".
        If a specific piece of information is missing, set its value to null.
        The "summary" field must contain a 200-word plain-language explanation of what the City is buying, from whom, for how much, and for how long.
        
        JSON SCHEMA:
        {{
            "contract_number": {{"value": "", "quote": "", "page": ""}},
            "vendor_name": {{"value": "", "quote": "", "page": ""}},
            "contract_type": {{"value": "", "quote": "", "page": ""}},
            "maximum_contract_amount": {{"value": "", "quote": "", "page": ""}},
            "commencement_date": {{"value": "", "quote": "", "page": ""}},
            "expiration_renewal_date": {{"value": "", "quote": "", "page": ""}},
            "department": {{"value": "", "quote": "", "page": ""}},
            "key_compliance_clauses": [
                {{"value": "", "quote": "", "page": ""}}
            ],
            "summary": ""
        }}
        
        Context:
        {context}
        
        JSON Output:""",
        input_variables=["context"]
    )
    chain = prompt | llm
    response = chain.invoke({"context": formatted_context})
    
    return {"answer": response.content}

def build_workflow(vector_store: PineconeVectorStore, llm: ChatGoogleGenerativeAI):
    workflow = StateGraph(GraphState)
    workflow.add_node("retrieve", lambda state: retrieve_node(state, vector_store))
    workflow.add_node("generate", lambda state: generate_node(state, llm))
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()

def initialize_vector_store(pinecone_key: str, google_key: str, index_name: str) -> PineconeVectorStore:
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=google_key
    )

    sample_vector = embeddings.embed_query("detect")
    detected_dimension = len(sample_vector)

    pc = Pinecone(api_key=pinecone_key)
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]

    if index_name not in existing_indexes:
        pc.create_index(
            name=index_name,
            dimension=detected_dimension,
            metric="cosine",
            spec=ServerlessSpec(cloud="aws", region="us-east-1")
        )
        while not pc.describe_index(index_name).status['ready']:
            time.sleep(1)

    return PineconeVectorStore(
        index_name=index_name,
        embedding=embeddings,
        pinecone_api_key=pinecone_key
    )

def process_and_embed_pdf(pdf_path: str, vector_store: PineconeVectorStore):
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    batch_size = 80
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        vector_store.add_documents(batch)
        if i + batch_size < len(chunks):
            time.sleep(1)