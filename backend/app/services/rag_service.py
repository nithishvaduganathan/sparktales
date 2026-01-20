"""RAG (Retrieval-Augmented Generation) service for AI-powered Q&A."""
from typing import List, Optional, Tuple
import time

from app.services.document_service import chunk_text


class SimpleRAGService:
    """
    Simple RAG service that performs keyword-based search on document content.
    In production, this would use embeddings and a vector database.
    """
    
    def __init__(self):
        self.documents: dict = {}  # document_id -> content
    
    def add_document(self, document_id: int, content: str):
        """Add a document to the RAG index."""
        self.documents[document_id] = content
    
    def remove_document(self, document_id: int):
        """Remove a document from the RAG index."""
        if document_id in self.documents:
            del self.documents[document_id]
    
    def search(self, query: str, document_ids: Optional[List[int]] = None, top_k: int = 3) -> List[Tuple[int, str]]:
        """
        Search for relevant document chunks based on the query.
        Returns a list of (document_id, relevant_chunk) tuples.
        """
        results = []
        query_words = set(query.lower().split())
        
        docs_to_search = document_ids if document_ids else list(self.documents.keys())
        
        for doc_id in docs_to_search:
            if doc_id not in self.documents:
                continue
            
            content = self.documents[doc_id]
            chunks = chunk_text(content, chunk_size=500, chunk_overlap=100)
            
            for chunk in chunks:
                chunk_words = set(chunk.lower().split())
                overlap = len(query_words.intersection(chunk_words))
                
                if overlap > 0:
                    results.append((doc_id, chunk, overlap))
        
        # Sort by relevance (overlap count)
        results.sort(key=lambda x: x[2], reverse=True)
        
        # Return top_k results without the score
        return [(doc_id, chunk) for doc_id, chunk, _ in results[:top_k]]
    
    def generate_response(self, query: str, document_ids: Optional[List[int]] = None) -> Tuple[str, int]:
        """
        Generate a response based on the query and relevant documents.
        Returns (response, processing_time_ms).
        """
        start_time = time.time()
        
        relevant_chunks = self.search(query, document_ids)
        
        if not relevant_chunks:
            response = "I couldn't find relevant information in the provided documents to answer your question. Please make sure you have uploaded documents containing the information you're looking for."
        else:
            # Combine relevant chunks
            context = "\n\n".join([chunk for _, chunk in relevant_chunks])
            
            # Generate a simple response (in production, this would use an LLM)
            response = f"Based on the documents you've uploaded, here is the relevant information:\n\n{context[:1500]}"
            
            if len(context) > 1500:
                response += "\n\n... (more content available in the documents)"
        
        processing_time = int((time.time() - start_time) * 1000)
        
        return response, processing_time


# Global RAG service instance
rag_service = SimpleRAGService()
