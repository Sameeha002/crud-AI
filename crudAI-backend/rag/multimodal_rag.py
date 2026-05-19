# This code opens your PDF, uses an AI model to intelligently identify and extract text, 
# tables, and images, then organizes everything into clean, reasonably-sized chunks ready to be 
# processed by an LLM.

from unstructured.partition.pdf import partition_pdf
import warnings
import base64
from IPython.display import Image, display
warnings.filterwarnings('ignore')

output_path = './rag/docs/'
file_path = output_path + 'Final_Wood_Bar_MidlandReport.pdf'

# step 1: partition and chunk the pdf
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


# step 2: Extract tables from chunks
def get_table(chunks):
    tables = []
    for chunk in chunks:
        for el in chunk.metadata.orig_elements:
            if 'Table' in str(type(el)):
                print(el.to_dict())
                tables.append(el)
    return tables

tables = get_table(chunks)
print(f"Total tables: {len(tables)}")

# step 3: Extract text chunks 
def save_texts(chunks):
    texts = [chunk for chunk in chunks if 'CompositeElement' in str(type(chunk))]
    return texts

texts = save_texts(chunks)
print(f"Number of text chunks: {len(texts)}")

#  Step 4: Extract images (base64) 
def get_image_base64(chunks):
    image_b64 = []
    for chunk in chunks:
        chunk_el = chunk.metadata.orig_elements
        for el in chunk_el:
            if 'Image' in str(type(el)):
                image_b64.append(el.metadata.image_base64)
    return image_b64

images = get_image_base64(chunks)
print(f"Total images extracted: {len(images)}")

def display_base64_image(base64_code):
    ## decode the base64 string to binary
    image_data = base64.b64decode(base64_code)
    # display the image
    display(Image(data=image_data))
    
display_base64_image(images[0])