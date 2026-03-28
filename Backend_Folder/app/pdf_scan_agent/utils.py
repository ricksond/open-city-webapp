# import time
# from typing import List, TypedDict
# from langchain_core.documents import Document
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from langchain_core.prompts import PromptTemplate
# from langgraph.graph import StateGraph, START, END
# from pinecone import Pinecone, ServerlessSpec

# # ==========================================
# # GRAPH STATE & NODES
# # ==========================================
# class GraphState(TypedDict):
#     question: str
#     context: List[Document]
#     answer: str

# def format_docs(docs: List[Document]) -> str:
#     formatted_texts = []
#     for doc in docs:
#         page_num = doc.metadata.get('page', 'Unknown')
#         formatted_texts.append(f"--- PAGE {page_num} ---\n{doc.page_content}")
#     return "\n\n".join(formatted_texts)

# def retrieve_node(state: GraphState, vector_store: PineconeVectorStore) -> dict:
#     # Retrieve top 5 similar documents
#     docs = vector_store.similarity_search(state["question"], k=5)
#     return {"context": docs}

# def generate_node(state: GraphState, llm: ChatGoogleGenerativeAI) -> dict:
#     formatted_context = format_docs(state["context"])
#     prompt = PromptTemplate(
#         template="""You are a precise document analysis assistant. 
#         Your task is to answer the user's question based strictly on the provided context.
        
#         CRITICAL RULE: You MUST quote the exact lines from the context to support your answer. 
#         Enclose the exact lines in quotation marks and cite the page number.
#         If the answer is not in the context, say "I cannot find the answer in the provided document." 
#         Do not use external knowledge.
        
#         Context:
#         {context}
        
#         Question: {question}
        
#         Answer (with exact quotes and page numbers):""",
#         input_variables=["context", "question"]
#     )
#     chain = prompt | llm
#     response = chain.invoke({"context": formatted_context, "question": state["question"]})
#     return {"answer": response.content}

# def build_workflow(vector_store: PineconeVectorStore, llm: ChatGoogleGenerativeAI):
#     workflow = StateGraph(GraphState)
#     workflow.add_node("retrieve", lambda state: retrieve_node(state, vector_store))
#     workflow.add_node("generate", lambda state: generate_node(state, llm))
#     workflow.add_edge(START, "retrieve")
#     workflow.add_edge("retrieve", "generate")
#     workflow.add_edge("generate", END)
#     return workflow.compile()

# # ==========================================
# # PINECONE INITIALIZATION (WITH AUTO-DETECT)
# # ==========================================
# def initialize_vector_store(pinecone_key: str, google_key: str, index_name: str) -> PineconeVectorStore:
#     # Using the latest embedding model
#     embeddings = GoogleGenerativeAIEmbeddings(
#         model="models/text-embedding-004", 
#         google_api_key=google_key
#     )
    
#     # 1. AUTO-DETECT: Ask the model for its dimension size by embedding a tiny string
#     print("Auto-detecting embedding dimensions from Google...")
#     sample_vector = embeddings.embed_query("detect")
#     detected_dimension = len(sample_vector)
#     print(f"[*] Detected dimension: {detected_dimension}")
    
#     pc = Pinecone(api_key=pinecone_key)
#     existing_indexes = [idx["name"] for idx in pc.list_indexes()]
    
#     if index_name not in existing_indexes:
#         print(f"[*] Creating new Pinecone index: '{index_name}' with {detected_dimension} dimensions...")
#         pc.create_index(
#             name=index_name,
#             dimension=detected_dimension, # Dynamically assigned!
#             metric="cosine",
#             spec=ServerlessSpec(cloud="aws", region="us-east-1")
#         )
#         while not pc.describe_index(index_name).status['ready']:
#             time.sleep(1)
#         print("[*] Index created successfully.")
#     else:
#         # Prevent the 400 Bad Request error by checking dimensions first
#         desc = pc.describe_index(index_name)
#         if desc.dimension != detected_dimension:
#             raise ValueError(
#                 f"Dimension Mismatch! Index '{index_name}' has {desc.dimension} dimensions, "
#                 f"but model outputs {detected_dimension}. Please delete the index in your Pinecone console."
#             )
            
#     return PineconeVectorStore(
#         index_name=index_name, 
#         embedding=embeddings, 
#         pinecone_api_key=pinecone_key
#     )







# import os
# import time
# from getpass import getpass
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from langchain_google_genai import ChatGoogleGenerativeAI

# from utils import initialize_vector_store, build_workflow

# def main():

#     # 1. Get Credentials
#     google_key = os.getenv("GOOGLE_API_KEY") or getpass("Enter Gemini API Key (Hidden): ")
#     pinecone_key = os.getenv("PINECONE_API_KEY") or getpass("Enter Pinecone API Key (Hidden): ")
    
#     pdf_path = input("\nEnter the relative or absolute path to your PDF file (e.g., sample.pdf): ")

#     if not os.path.exists(pdf_path):
#         return

#     # 2. Setup Vector Store & LLM
#     index_name = "pdf-scan-bot-index"
#     try:
#         vector_store = initialize_vector_store(
#             pinecone_key=pinecone_key, 
#             google_key=google_key, 
#             index_name=index_name
#         )
#     except Exception as e:
#         return

#     # Using Gemini 2.5 Flash
#     llm = ChatGoogleGenerativeAI(
#         model="gemini-2.5-flash", 
#         google_api_key=google_key
#     )

#     # 3. Process PDF (with rate limit handling)
#     loader = PyPDFLoader(pdf_path)
#     docs = loader.load()
    
#     splitter = RecursiveCharacterTextSplitter(chunk_size=1200, chunk_overlap=200)
#     chunks = splitter.split_documents(docs)
    
    
#     # We ask before uploading so you don't accidentally burn quotas re-uploading the same file
#     ans = input("Do you want to upload/index these chunks to Pinecone now? (y/n): ")
#     if ans.lower() == 'y':
#         batch_size = 80
#         for i in range(0, len(chunks), batch_size):
#             batch = chunks[i : i + batch_size]
#             vector_store.add_documents(batch)
            
#             if i + batch_size < len(chunks):
#                 time.sleep(60)


#     # 4. Compile Graph
#     app = build_workflow(vector_store, llm)

#     # 5. Interactive Chat Loop

#     while True:
#         prompt = input("\n👤 You: ")
        
#         if prompt.lower() in ['exit', 'quit']:
#             print("Exiting chat. Goodbye!")
#             break
            
#         if not prompt.strip():
#             continue

#         print("🤖 Assistant is typing...")
#         try:
#             # Invoke the LangGraph workflow
#             response = app.invoke({"question": prompt})
#             print(f"\n{response['answer']}")
#         except Exception as e:
#             print(f"\n[!] An error occurred during chat: {e}")

# if __name__ == "__main__":
#     main()