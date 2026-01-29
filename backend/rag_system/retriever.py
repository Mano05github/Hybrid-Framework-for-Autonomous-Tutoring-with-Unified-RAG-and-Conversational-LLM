import os
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
import logging

logger = logging.getLogger(__name__)

# Same as ingest.py
PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")

class RAGRetriever:
    def __init__(self):
        self.db = None
        self._initialize_db()

    def _initialize_db(self):
        """
        Initialize the Vector DB connection.
        """
        if not os.path.exists(PERSIST_DIRECTORY):
            logger.warning(f"RAG Storage not found at {PERSIST_DIRECTORY}. Please run ingest.py first.")
            return

        try:
            embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
            self.db = Chroma(persist_directory=PERSIST_DIRECTORY, embedding_function=embedding_function)
            logger.info("RAG Retriever initialized properly.")
        except Exception as e:
            logger.error(f"Failed to initialize RAG DB: {e}")

    def get_relevant_context(self, query: str, k: int = 3) -> str:
        """
        Search for top k documents and return them as a single string.
        """
        if not self.db:
            return ""

        try:
            # Search
            docs = self.db.similarity_search(query, k=k)
            if not docs:
                return ""
            
            # Combine text
            context_text = "\n\n".join([f"[Source: {d.metadata.get('source', 'Unknown')}]\n{d.page_content}" for d in docs])
            return context_text
        except Exception as e:
            logger.error(f"RAG Retrieval Error: {e}")
            return ""
