import time
from typing import List, TypedDict
from langchain_core.documents import Document
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from langchain_pinecone import PineconeVectorStore
from langchain_core.prompts import PromptTemplate
from langgraph.graph import StateGraph, START, END
from pinecone import Pinecone, ServerlessSpec
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter

# ==========================================
# GRAPH STATE & NODES
# ==========================================


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
    docs = vector_store.similarity_search(state["question"], k=5)
    return {"context": docs}


def generate_node(state: GraphState, llm: ChatGoogleGenerativeAI) -> dict:
    formatted_context = format_docs(state["context"])

    # Strictly instruct the LLM to only return exact quotes and page numbers
    prompt = PromptTemplate(
        template="""You are an automated extraction system. 
        Extract information answering the question based strictly on the provided context.
        
        CRITICAL RULES:
        1. You MUST extract the exact, verbatim lines from the text.
        2. Enclose the extracted text in quotation marks ("").
        3. Append the exact page number next to the quote (e.g., [Page 4]).
        4. If the information is not present in the context, output exactly: "Not found in document."
        5. Do not add conversational filler, summaries, or explanations. Just the quotes and pages.
        
        Context:
        {context}
        
        Question: {question}
        
        Extraction (Exact quotes and page numbers only):""",
        input_variables=["context", "question"]
    )
    chain = prompt | llm
    response = chain.invoke(
        {"context": formatted_context, "question": state["question"]})
    return {"answer": response.content}


def build_workflow(vector_store: PineconeVectorStore, llm: ChatGoogleGenerativeAI):
    workflow = StateGraph(GraphState)
    workflow.add_node(
        "retrieve", lambda state: retrieve_node(state, vector_store))
    workflow.add_node("generate", lambda state: generate_node(state, llm))
    workflow.add_edge(START, "retrieve")
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    return workflow.compile()

# ==========================================
# PINECONE INITIALIZATION
# ==========================================


def initialize_vector_store(pinecone_key: str, google_key: str, index_name: str) -> PineconeVectorStore:
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/gemini-embedding-001",
        google_api_key=google_key
    )

    print("Auto-detecting embedding dimensions from Google...")
    sample_vector = embeddings.embed_query("detect")
    detected_dimension = len(sample_vector)

    pc = Pinecone(api_key=pinecone_key)
    existing_indexes = [idx["name"] for idx in pc.list_indexes()]

    if index_name not in existing_indexes:
        print(f"[*] Creating new Pinecone index: '{index_name}'...")
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

# ==========================================
# PDF PROCESSING & EMBEDDING
# ==========================================


def process_and_embed_pdf(pdf_path: str, vector_store: PineconeVectorStore):
    """Loads, chunks, and pushes PDF to Pinecone"""
    loader = PyPDFLoader(pdf_path)
    docs = loader.load()

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1200, chunk_overlap=200)
    chunks = splitter.split_documents(docs)

    batch_size = 80
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i: i + batch_size]
        vector_store.add_documents(batch)
        if i + batch_size < len(chunks):
            time.sleep(1)  # Minor pause between API batches
