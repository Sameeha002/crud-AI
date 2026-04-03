import fitz  
from llama_index.core import Document, Settings, StorageContext, VectorStoreIndex
from llama_index.core.node_parser import SentenceSplitter
from llama_index.embeddings.huggingface import HuggingFaceEmbedding
from llama_index.vector_stores.chroma import ChromaVectorStore
import chromadb

print("Loading embedding model...")
embed_model = HuggingFaceEmbedding(
    model_name="sentence-transformers/all-MiniLM-L6-v2",
    embed_batch_size=32,
)
Settings.embed_model = embed_model

# Extract text with PyMuPDF
print("Extracting text from PDF...")
pdf_path = r"E:\uv-project\crudAI-backend\rag\docs\Novel.pdf"
doc = fitz.open(pdf_path)

documents = []
for page_num, page in enumerate(doc):
    text = page.get_text("text")
    if text.strip():
        documents.append(Document(
            text=text,
            metadata={"page": page_num + 1}
        ))
doc.close()

print(f"Extracted {len(documents)} pages")

# Chunk
splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = splitter.get_nodes_from_documents(documents)
print(f"\nTotal chunks: {len(nodes)}")

# chromadb storage
chroma_client = chromadb.PersistentClient(path="rag/storage")
chroma_collection = chroma_client.get_or_create_collection("novel_rag")

vector_store = ChromaVectorStore(chroma_collection=chroma_collection)
storage_context = StorageContext.from_defaults(vector_store=vector_store)

print("\nGenerating embeddings...")
index = VectorStoreIndex(nodes, storage_context=storage_context, show_progress=True)
print(f"\nDone! {chroma_collection.count()} embeddings stored.")