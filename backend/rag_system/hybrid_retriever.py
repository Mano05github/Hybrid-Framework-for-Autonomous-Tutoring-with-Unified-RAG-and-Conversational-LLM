"""
Omni-RAG Hybrid Retriever - Advanced Multi-Modal Retrieval System

Implements:
1. Hybrid Search (Vector + BM25 Keyword)
2. Reciprocal Rank Fusion
3. Cross-Encoder Re-Ranking
4. Context Compression

Author: Vaathiyar Team
Phase: 9 (Omni-RAG Implementation)
"""

import os
import logging
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_chroma import Chroma
import numpy as np
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import SentenceTransformerEmbeddings
from langchain_community.retrievers import BM25Retriever
from langchain_core.documents import Document
from sentence_transformers import CrossEncoder
import spacy

logger = logging.getLogger(__name__)

# Storage path
PERSIST_DIRECTORY = os.path.join(os.path.dirname(os.path.abspath(__file__)), "storage")


class SimpleEnsembleRetriever:
    """Custom Ensemble Retriever - replaces missing langchain EnsembleRetriever"""
    
    def __init__(self, retrievers: List, weights: List[float]):
        self.retrievers = retrievers
        self.weights = weights
    
    def get_relevant_documents(self, query: str) -> List[Document]:
        all_results = {}
        for retriever, weight in zip(self.retrievers, self.weights):
            try:
                docs = retriever.get_relevant_documents(query)
                for rank, doc in enumerate(docs, 1):
                    doc_key = doc.page_content[:100]
                    rrf_score = weight / (rank + 60)
                    if doc_key in all_results:
                        all_results[doc_key]['score'] += rrf_score
                    else:
                        all_results[doc_key] = {'doc': doc, 'score': rrf_score}
            except:
                continue
        sorted_results = sorted(all_results.values(), key=lambda x: x['score'], reverse=True)
        return [result['doc'] for result in sorted_results]


@dataclass
class RetrievalResult:
    """Structured retrieval result with metadata."""
    content: str
    source: str
    score: float
    rank: int
    method: str  # 'vector', 'keyword', 'hybrid'


class HybridRetriever:
    """
    Advanced Hybrid Retriever combining Vector Search, BM25, and Re-Ranking.
    
    Architecture:
        Query -> [Vector Search + BM25 Search] -> RRF Fusion -> Cross-Encoder Re-Rank -> Top K
    """
    
    def __init__(
        self,
        vector_weight: float = 0.5,
        bm25_weight: float = 0.5,
        use_reranker: bool = True,
        reranker_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2",
        top_k: int = 20,
        final_k: int = 3
    ):
        """
        Initialize Hybrid Retriever.
        
        Args:
            vector_weight: Weight for vector search (0-1)
            bm25_weight: Weight for BM25 search (0-1)
            use_reranker: Whether to use cross-encoder re-ranking
            reranker_model: HuggingFace cross-encoder model name
            top_k: Number of candidates to retrieve before re-ranking
            final_k: Final number of results to return after re-ranking
        """
        self.vector_weight = vector_weight
        self.bm25_weight = bm25_weight
        self.use_reranker = use_reranker
        self.top_k = top_k
        self.final_k = final_k
        
        # Initialize components
        self.vector_db = None
        self.bm25_retriever = None
        self.ensemble_retriever = None
        self.reranker = None
        self.nlp = None
        
        # Load models
        self._initialize_retrievers()
        if use_reranker:
            self._initialize_reranker(reranker_model)
        
        logger.info(f"HybridRetriever initialized (vector: {vector_weight}, bm25: {bm25_weight}, rerank: {use_reranker})")
    
    def _initialize_retrievers(self):
        """Initialize vector DB and BM25 retrievers."""
        if not os.path.exists(PERSIST_DIRECTORY):
            logger.warning(f"RAG Storage not found at {PERSIST_DIRECTORY}. Please run ingest.py first.")
            return
        
        try:
            # Vector Retriever (ChromaDB)
            embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
            self.vector_db = Chroma(
                persist_directory=PERSIST_DIRECTORY,
                embedding_function=embedding_function
            )
            
            # BM25 Retriever (Keyword Search)
            # Load all documents from ChromaDB for BM25 indexing
            all_docs = self._load_all_documents()
            if all_docs:
                self.bm25_retriever = BM25Retriever.from_documents(all_docs)
                self.bm25_retriever.k = self.top_k
                
                # Create Ensemble Retriever
                vector_retriever = self.vector_db.as_retriever(search_kwargs={"k": self.top_k})
                self.ensemble_retriever = SimpleEnsembleRetriever(
    retrievers=[vector_retriever, self.bm25_retriever],
    weights=[self.vector_weight, self.bm25_weight]
)
                
                logger.info(f"Hybrid retrieval ready: {len(all_docs)} documents indexed")
            else:
                logger.warning("No documents found for BM25 indexing")
        
        except Exception as e:
            logger.error(f"Failed to initialize retrievers: {e}")
    
    def _load_all_documents(self) -> List[Document]:
        """Load all documents from ChromaDB for BM25 indexing."""
        try:
            # Retrieve all docs using a generic query
            results = self.vector_db.get()
            docs = []
            
            if results and 'documents' in results:
                for i, text in enumerate(results['documents']):
                    metadata = results['metadatas'][i] if 'metadatas' in results else {}
                    docs.append(Document(page_content=text, metadata=metadata))
            
            return docs
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
    
    def _initialize_reranker(self, model_name: str):
        """Initialize cross-encoder re-ranker."""
        try:
            self.reranker = CrossEncoder(model_name)
            logger.info(f"Re-ranker loaded: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load re-ranker: {e}")
            self.use_reranker = False
    
    def retrieve(
        self,
        query: str,
        k: Optional[int] = None,
        method: str = "hybrid"
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant documents using hybrid search.
        
        Args:
            query: Search query
            k: Number of results to return (default: self.final_k)
            method: 'hybrid', 'vector', or 'keyword'
        
        Returns:
            List of RetrievalResult objects
        """
        k = k or self.final_k
        
        if not self.vector_db:
            logger.error("Vector DB not initialized")
            return []
        
        try:
            # Step 1: Initial Retrieval
            if method == "hybrid" and self.ensemble_retriever:
                docs = self.ensemble_retriever.get_relevant_documents(query)
                retrieval_method = "hybrid"
            elif method == "keyword" and self.bm25_retriever:
                docs = self.bm25_retriever.get_relevant_documents(query)
                retrieval_method = "keyword"
            else:
                # Fallback to vector search
                docs = self.vector_db.similarity_search(query, k=self.top_k)
                retrieval_method = "vector"
            
            if not docs:
                logger.warning(f"No documents retrieved for query: {query}")
                return []
            
            logger.info(f"Initial retrieval: {len(docs)} candidates ({retrieval_method})")
            
            # Step 2: Re-Ranking (if enabled)
            if self.use_reranker and self.reranker and len(docs) > 0:
                docs = self._rerank_documents(query, docs)
                logger.info(f"After re-ranking: top {min(k, len(docs))} results")
            
            # Step 3: Convert to RetrievalResult
            results = []
            for rank, doc in enumerate(docs[:k], 1):
                results.append(RetrievalResult(
                    content=doc.page_content,
                    source=doc.metadata.get('source', 'Unknown'),
                    score=doc.metadata.get('score', 0.0),
                    rank=rank,
                    method=retrieval_method
                ))
            
            return results
        
        except Exception as e:
            logger.error(f"Retrieval error: {e}")
            return []
    
    def _rerank_documents(self, query: str, docs: List[Document]) -> List[Document]:
        """
        Re-rank documents using cross-encoder.
        
        Args:
            query: Search query
            docs: List of candidate documents
        
        Returns:
            Re-ranked list of documents
        """
        try:
            # Create query-document pairs
            pairs = [[query, doc.page_content] for doc in docs]
            
            # Get scores from cross-encoder
            scores = self.reranker.predict(pairs)
            
            # Sort documents by score (descending)
            scored_docs = list(zip(docs, scores))
            scored_docs.sort(key=lambda x: x[1], reverse=True)
            
            # Add scores to metadata
            reranked_docs = []
            for doc, score in scored_docs:
                doc.metadata['rerank_score'] = float(score)
                doc.metadata['score'] = float(score)
                reranked_docs.append(doc)
            
            return reranked_docs
        
        except Exception as e:
            logger.error(f"Re-ranking error: {e}")
            return docs
    
    def get_context_string(
        self,
        query: str,
        k: Optional[int] = None,
        compress: bool = False
    ) -> str:
        """
        Retrieve and format context as a single string.
        
        Args:
            query: Search query
            k: Number of results
            compress: Whether to apply context compression
        
        Returns:
            Formatted context string
        """
        results = self.retrieve(query, k=k)
        
        if not results:
            return ""
        
        # Optional: Context Compression
        if compress:
            results = self._compress_context(query, results)
        
        # Format as string
        context_parts = []
        for result in results:
            context_parts.append(
                f"[Source: {result.source} | Rank: {result.rank} | Score: {result.score:.3f}]\n"
                f"{result.content}\n"
            )
        
        return "\n".join(context_parts)
    
    def _compress_context(self, query: str, results: List[RetrievalResult]) -> List[RetrievalResult]:
        """
        Extract only relevant sentences from retrieved chunks (context compression).
        
        Args:
            query: Original query
            results: Retrieved results
        
        Returns:
            Compressed results with only relevant sentences
        """
        if not self.nlp:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except:
                logger.warning("spaCy model not found. Install: python -m spacy download en_core_web_sm")
                return results
        
        compressed_results = []
        query_terms = set(query.lower().split())
        
        for result in results:
            doc = self.nlp(result.content)
            relevant_sentences = []
            
            for sent in doc.sents:
                sent_text = sent.text.lower()
                # Keep sentence if it contains query terms
                if any(term in sent_text for term in query_terms):
                    relevant_sentences.append(sent.text.strip())
            
            if relevant_sentences:
                compressed_content = " ".join(relevant_sentences)
                result.content = compressed_content
                compressed_results.append(result)
        
        return compressed_results if compressed_results else results


class ContextCompressor:
    """
    Advanced context compression using extractive summarization.
    Reduces noise and token cost by keeping only relevant sentences.
    """
    
    def __init__(self):
        self.nlp = None
        self._load_nlp()
    
    def _load_nlp(self):
        """Load spaCy NLP model."""
        try:
            self.nlp = spacy.load("en_core_web_sm")
            logger.info("Context compressor initialized")
        except:
            logger.warning("spaCy not available. Run: python -m spacy download en_core_web_sm")
    
    def compress(self, query: str, documents: List[str], threshold: float = 0.3) -> List[str]:
        """
        Compress documents by extracting only relevant sentences.
        
        Args:
            query: Original query
            documents: List of document texts
            threshold: Relevance threshold (0-1)
        
        Returns:
            List of compressed documents
        """
        if not self.nlp:
            return documents
        
        query_doc = self.nlp(query.lower())
        query_terms = set([token.lemma_ for token in query_doc if not token.is_stop])
        
        compressed_docs = []
        for doc_text in documents:
            doc = self.nlp(doc_text)
            relevant_sentences = []
            
            for sent in doc.sents:
                sent_terms = set([token.lemma_ for token in sent if not token.is_stop])
                # Calculate overlap
                overlap = len(query_terms & sent_terms) / max(len(query_terms), 1)
                
                if overlap >= threshold:
                    relevant_sentences.append(sent.text.strip())
            
            compressed_text = " ".join(relevant_sentences) if relevant_sentences else doc_text[:500]
            compressed_docs.append(compressed_text)
        
        return compressed_docs


# Singleton instance
_hybrid_retriever_instance = None

def get_hybrid_retriever() -> HybridRetriever:
    """Get singleton instance of HybridRetriever."""
    global _hybrid_retriever_instance
    if _hybrid_retriever_instance is None:
        _hybrid_retriever_instance = HybridRetriever()
    return _hybrid_retriever_instance
