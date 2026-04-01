from llama_index.core import SimpleDirectoryReader
from llama_index.core.node_parser import SentenceSplitter


# Load your PDF
documents = SimpleDirectoryReader(
    input_files=[r"E:\uv-project\crudAI-backend\rag\docs\Novel.pdf"]
).load_data()

# Split into chunks
splitter = SentenceSplitter(chunk_size=512, chunk_overlap=50)
nodes = splitter.get_nodes_from_documents(documents)

# print(f"Total chunks: {len(nodes)}")

# create embeddingsf