from llama_index.core import Settings, VectorStoreIndex
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.llms.groq import Groq 
from llama_index.vector_stores.chroma import ChromaVectorStore
from llama_index.core import StorageContext
import chromadb
import os
from dotenv import load_dotenv

load_dotenv()
print("API Key loaded:", bool(os.getenv("GROQ_API_KEY")))

# Setup embedding model 
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    embed_batch_size=32,  
)
Settings.embed_model = embed_model

# Setup Gemini as LLM
llm = Groq(
    model="llama-3.1-8b-instant",
    api_key=os.getenv("GROQ_API_KEY"),
)
Settings.llm = llm

# Load existing Chroma index from disk
chroma_client = chromadb.PersistentClient(path="rag/storage")
chroma_collection = chroma_client.get_collection("novel_rag")

print(f"Loaded {chroma_collection.count()} embedded chunks from disk")

# Connect to LlamaIndex
vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

# Load index from existing vector store (no re-embedding)
index = VectorStoreIndex.from_vector_store(
    vector_store,
    storage_context=storage_context,
)

# Create query engine
query_engine = index.as_query_engine(similarity_top_k=5)

# Ask a question
question = "What is the main story about?"
print(f"\nQuestion: {question}")

response = query_engine.query(question)
print(f"\nAnswer: {response}")