# import os
# import time
# import streamlit as st
# from typing import List, TypedDict
# from langchain_core.documents import Document
# from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
# from langchain_pinecone import PineconeVectorStore
# from langchain_core.prompts import PromptTemplate
# from langgraph.graph import StateGraph, START, END
# from langchain_community.document_loaders import PyPDFLoader
# from langchain_text_splitters import RecursiveCharacterTextSplitter
# from pinecone import Pinecone, ServerlessSpec

# # ==========================================
# # 1. GRAPH STATE & NODES
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
#     # Uses the top 5 documents for context
#     docs = vector_store.similarity_search(state["question"], k=5)
#     return {"context": docs}


# def generate_node(state: GraphState, llm: ChatGoogleGenerativeAI) -> dict:
#     formatted_context = format_docs(state["context"])
#     prompt = PromptTemplate(
#         template="""You are a precise document analysis assistant. 
#         Answer based strictly on the context. Quote exact lines and cite page numbers.
#         If not in context, say "I cannot find the answer in the provided document."
        
#         Context: {context}
        
#         Question: {question}
        
#         Answer:""",
#         input_variables=["context", "question"]
#     )
#     chain = prompt | llm
#     response = chain.invoke(
#         {"context": formatted_context, "question": state["question"]})
#     return {"answer": response.content}


# def build_workflow(vector_store, llm):
#     workflow = StateGraph(GraphState)
#     workflow.add_node(
#         "retrieve", lambda state: retrieve_node(state, vector_store))
#     workflow.add_node("generate", lambda state: generate_node(state, llm))
#     workflow.add_edge(START, "retrieve")
#     workflow.add_edge("retrieve", "generate")
#     workflow.add_edge("generate", END)
#     return workflow.compile()

# # ==========================================
# # 2. VECTOR STORE INITIALIZATION
# # ==========================================


# def initialize_vector_store(pinecone_key: str, google_key: str, index_name: str):
#     # 1. Initialize the embedding model
#     embeddings = GoogleGenerativeAIEmbeddings(
#         model="models/gemini-embedding-001",
#         google_api_key=google_key
#     )

#     # 2. AUTO-DETECT: Ask the model for its dimension by embedding a tiny string
#     sample_vector = embeddings.embed_query("detect")
#     # This will be 3072 or 768 automatically
#     detected_dimension = len(sample_vector)

#     pc = Pinecone(api_key=pinecone_key)
#     active_indexes = [idx["name"] for idx in pc.list_indexes()]

#     # 3. Use the detected dimension to create the index
#     if index_name not in active_indexes:
#         st.info(
#             f"Auto-detected dimension: {detected_dimension}. Creating index...")
#         pc.create_index(
#             name=index_name,
#             dimension=detected_dimension,  # Dynamically assigned!
#             metric="cosine",
#             spec=ServerlessSpec(cloud="aws", region="us-east-1")
#         )
#         while not pc.describe_index(index_name).status['ready']:
#             time.sleep(1)
#     else:
#         # Check if the existing index matches what the model just told us
#         idx_desc = pc.describe_index(index_name)
#         if idx_desc.dimension != detected_dimension:
#             st.error(
#                 f"Mismatch! Index is {idx_desc.dimension}, but model is {detected_dimension}.")
#             st.stop()

#     return PineconeVectorStore(
#         index_name=index_name,
#         embedding=embeddings,
#         pinecone_api_key=pinecone_key
#     )


# # ==========================================
# # 3. STREAMLIT UI
# # ==========================================
# st.set_page_config(page_title="Gemini PDF Bot", page_icon="🤖")
# st.title("🤖 Gemini PDF Chat (LangGraph + Pinecone)")

# # Sidebar for Keys and File Upload
# with st.sidebar:
#     st.header("🔑 API Configuration")
#     user_gemini_key = st.text_input(
#         "Gemini API Key", type="password", placeholder="AIza...")
#     user_pinecone_key = st.text_input(
#         "Pinecone API Key", type="password", placeholder="pcsk_...")

#     st.divider()

#     uploaded_file = st.file_uploader("Upload Document (PDF)", type="pdf")

#     if st.button("Clear Chat History"):
#         st.session_state.messages = []
#         st.rerun()

# # Session State for chat persistence
# if "messages" not in st.session_state:
#     st.session_state.messages = []

# # Main Logic: Requires both keys and a file
# if user_gemini_key and user_pinecone_key and uploaded_file:

#     # 1. Setup Vector Store & LLM
#     try:
#         vector_store = initialize_vector_store(
#             user_pinecone_key,
#             user_gemini_key,
#             "pdf-scan-bot-index"
#         )

#         llm = ChatGoogleGenerativeAI(
#             model="gemini-2.5-flash",
#             google_api_key=user_gemini_key
#         )

#         # 2. Process File (Only if it's a new file)
#         if "current_file" not in st.session_state or st.session_state.current_file != uploaded_file.name:
#             with st.spinner("Analyzing and indexing PDF..."):
#                 with open("temp_upload.pdf", "wb") as f:
#                     f.write(uploaded_file.getbuffer())

#                 loader = PyPDFLoader("temp_upload.pdf")
#                 docs = loader.load()
#                 splitter = RecursiveCharacterTextSplitter(
#                     chunk_size=1000, chunk_overlap=100)
#                 chunks = splitter.split_documents(docs)

#                 vector_store.add_documents(chunks)
#                 st.session_state.current_file = uploaded_file.name
#                 st.success("Indexing complete!")

#         # 3. Compile Graph
#         app = build_workflow(vector_store, llm)

#         # 4. Chat Interface
#         for msg in st.session_state.messages:
#             with st.chat_message(msg["role"]):
#                 st.markdown(msg["content"])

#         if prompt := st.chat_input("Ask a question about your PDF"):
#             st.session_state.messages.append(
#                 {"role": "user", "content": prompt})
#             with st.chat_message("user"):
#                 st.markdown(prompt)

#             with st.chat_message("assistant"):
#                 with st.spinner("Searching document..."):
#                     response = app.invoke({"question": prompt})
#                     answer = response["answer"]
#                     st.markdown(answer)
#                     st.session_state.messages.append(
#                         {"role": "assistant", "content": answer})

#     except Exception as e:
#         st.error(f"An error occurred: {str(e)}")

# else:
#     st.warning(
#         "Please enter both API keys in the sidebar and upload a PDF to start chatting.")
