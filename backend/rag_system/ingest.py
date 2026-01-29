import os
from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
import logging

# Configure Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SOURCE_DIRECTORY = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "source_documents")
PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")

def load_documents():
    """
    Load all PDFs from the source directory.
    """
    if not os.path.exists(SOURCE_DIRECTORY):
        os.makedirs(SOURCE_DIRECTORY)
        logger.warning(f"Source directory {SOURCE_DIRECTORY} created. Please add PDFs there.")
        return []

    logger.info(f"Loading documents from {SOURCE_DIRECTORY}")
    loader = DirectoryLoader(SOURCE_DIRECTORY, glob="**/*.pdf", loader_cls=PyPDFLoader)
    documents = loader.load()
    return documents

def ingest_docs():
    """
    Main ingestion logic: Load -> Split -> Embed -> Store.
    """
    # 1. Load Documents
    documents = load_documents()
    if not documents:
        logger.warning("No documents found to ingest.")
        return

    logger.info(f"Loaded {len(documents)} document(s).")

    # 2. Split Text
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    texts = text_splitter.split_documents(documents)
    logger.info(f"Split into {len(texts)} chunks.")

    # 3. Create Embeddings & Vector Store
    # using all-MiniLM-L6-v2 which is fast and runs on CPU
    embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
    
    logger.info("Creating Vector Database... (This might take a moment)")
    db = Chroma.from_documents(
        documents=texts, 
        embedding=embedding_function, 
        persist_directory=PERSIST_DIRECTORY
    )
    
    # 4. Persist
    # Chroma 0.4+ persists automatically, but explicit call is safe for older versions
    db.persist()
    db = None 

    logger.info(f"Ingestion Complete! Knowledge stored in {PERSIST_DIRECTORY}")

if __name__ == "__main__":
    ingest_docs()
