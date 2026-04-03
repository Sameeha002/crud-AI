from unstructured.partition.pdf import partition_pdf
import warnings
warnings.filterwarnings('ignore')

output_path = './rag/docs/'
file_path = output_path + 'Final_Wood_Bar_MidlandReport.pdf'

def partition_and_chunk_pdf(file_path):
    """Partitions and chunks a PDF file into manageable pieces. 
    """
    chunks= partition_pdf(
        filename=file_path,
        infer_tables_structure=True,          # Extract tables with structure
        strategy='hi_res',                     # Mandatory to infer tables
        
        extract_image_block_types=["Image"],   # Add 'Table' to list to extract tables as images
        # image_output_dir_path=output_path,    # Directory to save images
        
        extract_image_block_to_payload=True,   # Extract metadata element containing base64 object of the image
                                                # Must when sending the image to LLMs
        
        chunking_strategy="by_title",          # Chunking strategy to use, can be 'by_title', 'basic'
        max_characters=2000,                   # Maximum number of characters per chunk
        combine_text_under_n_chars=500,        # Combine text blocks under this number of characters with previous text block
        new_after_n_chars=6000,                # New chunk after this number of characters. Hard limit.
    )
    return chunks

chunks = partition_and_chunk_pdf(file_path)
print(set([str(type(el)) for el in chunks]))  
print(f"Total chunks: {len(chunks)}")       