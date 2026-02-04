"""
RAG (Retrieval-Augmented Generation) Service using Gemini 2.5 Flash
Processes PDFs, creates embeddings, and provides course-specific AI chat
"""
import os
import io
import json
import hashlib
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

import boto3
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


@dataclass
class DocumentChunk:
    """Represents a chunk of document text with metadata"""
    text: str
    course_id: int
    resource_id: int
    page_number: int
    chunk_index: int
    embedding: Optional[List[float]] = None


class RAGService:
    """
    RAG Service for course-specific document retrieval and AI chat
    Uses Gemini 2.5 Flash for embeddings and generation
    Uses PostgreSQL with pgvector for vector storage
    """
    
    def __init__(self):
        # Load settings from pydantic config (reads .env file)
        from app.config import get_settings
        settings = get_settings()
        
        self.gemini_api_key = settings.gemini_api_key
        self.s3_client = boto3.client(
            's3',
            region_name=settings.aws_region,
            aws_access_key_id=settings.aws_access_key_id,
            aws_secret_access_key=settings.aws_secret_access_key,
        )
        self.bucket_name = settings.s3_bucket_name
        self._client = None
        self._model = None
        
    @property
    def client(self):
        """Lazy load Google GenAI client"""
        if self._client is None:
            if not self.gemini_api_key:
                raise ValueError("GEMINI_API_KEY not configured in .env file")
            try:
                from google import genai
                self._client = genai.Client(api_key=self.gemini_api_key)
            except ImportError:
                raise ImportError("google-genai not installed. Run: pip install google-genai")
        return self._client
    
    def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for text using Gemini embedding model
        """
        try:
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            raise

    def get_query_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a query
        """
        try:
            result = self.client.models.embed_content(
                model="text-embedding-004",
                contents=text,
            )
            return result.embeddings[0].values
        except Exception as e:
            logger.error(f"Error generating query embedding: {e}")
            raise

    def generate_content(self, prompt: str) -> str:
        """
        Generate content using Gemini 2.5 Flash
        """
        try:
            response = self.client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
            )
            return response.text
        except Exception as e:
            logger.error(f"Error generating content: {e}")
            raise

    def extract_text_from_pdf(self, pdf_content: bytes) -> List[Dict[str, Any]]:
        """
        Extract text from PDF, returning list of pages with text
        """
        try:
            import pypdf
            
            pdf_file = io.BytesIO(pdf_content)
            reader = pypdf.PdfReader(pdf_file)
            
            pages = []
            for i, page in enumerate(reader.pages):
                text = page.extract_text() or ""
                if text.strip():
                    pages.append({
                        "page_number": i + 1,
                        "text": text.strip()
                    })
            
            return pages
            
        except ImportError:
            raise ImportError("pypdf not installed. Run: pip install pypdf")
        except Exception as e:
            logger.error(f"Error extracting PDF text: {e}")
            raise

    def chunk_text(self, text: str, chunk_size: int = 1000, overlap: int = 200) -> List[str]:
        """
        Split text into overlapping chunks for better context retention
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            
            # Try to break at sentence or paragraph boundary
            if end < len(text):
                # Look for paragraph break first
                para_break = text.rfind('\n\n', start, end)
                if para_break > start + chunk_size // 2:
                    end = para_break
                else:
                    # Look for sentence break
                    sent_break = text.rfind('. ', start, end)
                    if sent_break > start + chunk_size // 2:
                        end = sent_break + 1
            
            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)
            
            start = end - overlap if end < len(text) else len(text)
        
        return chunks

    def download_from_s3(self, file_url: str) -> bytes:
        """
        Download file from S3 given its URL
        """
        try:
            # Extract key from URL
            # URL format: https://bucket.s3.region.amazonaws.com/key
            key = file_url.split(".amazonaws.com/")[1]
            
            response = self.s3_client.get_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return response['Body'].read()
        except Exception as e:
            logger.error(f"Error downloading from S3: {e}")
            raise

    async def process_pdf_for_rag(
        self,
        course_id: int,
        resource_id: int,
        file_url: str,
        db: Session
    ) -> int:
        """
        Process a PDF file: extract text, chunk, create embeddings, store in vector DB
        Returns number of chunks created
        """
        try:
            # Download PDF from S3
            pdf_content = self.download_from_s3(file_url)
            
            # Extract text from PDF
            pages = self.extract_text_from_pdf(pdf_content)
            
            if not pages:
                logger.warning(f"No text extracted from PDF resource {resource_id}")
                return 0
            
            # Delete existing chunks for this resource (in case of re-processing)
            db.execute(
                text("DELETE FROM document_chunks WHERE resource_id = :resource_id"),
                {"resource_id": resource_id}
            )
            
            chunks_created = 0
            
            for page in pages:
                # Chunk the page text
                chunks = self.chunk_text(page["text"])
                
                for i, chunk_text in enumerate(chunks):
                    # Generate embedding
                    embedding = self.get_embedding(chunk_text)
                    
                    # Store chunk with embedding in database
                    db.execute(
                        text("""
                            INSERT INTO document_chunks 
                            (course_id, resource_id, page_number, chunk_index, content, embedding)
                            VALUES (:course_id, :resource_id, :page_number, :chunk_index, :content, :embedding)
                        """),
                        {
                            "course_id": course_id,
                            "resource_id": resource_id,
                            "page_number": page["page_number"],
                            "chunk_index": i,
                            "content": chunk_text,
                            "embedding": json.dumps(embedding)
                        }
                    )
                    chunks_created += 1
            
            db.commit()
            logger.info(f"Created {chunks_created} chunks for resource {resource_id}")
            return chunks_created
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error processing PDF for RAG: {e}")
            raise

    def search_similar_chunks(
        self,
        query: str,
        course_id: int,
        db: Session,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Search for chunks similar to query within a specific course
        Uses cosine similarity for vector search
        """
        try:
            # First check if table exists to avoid transaction errors
            try:
                table_check = db.execute(
                    text("SELECT 1 FROM document_chunks LIMIT 1")
                )
                table_check.fetchone()
            except Exception:
                # Table doesn't exist yet - rollback and return empty
                db.rollback()
                logger.warning("document_chunks table not found. Run migrations first.")
                return []
            
            # Get query embedding
            query_embedding = self.get_query_embedding(query)
            
            # Try to search - fallback to Python similarity if pgvector not available
            try:
                # Load all chunks for this course and compute similarity in Python
                # (More compatible than pgvector which requires extension)
                result = db.execute(
                    text("""
                        SELECT id, content, page_number, resource_id, embedding
                        FROM document_chunks
                        WHERE course_id = :course_id
                    """),
                    {"course_id": course_id}
                )
                
                rows = result.fetchall()
                if not rows:
                    return []
                
                # Compute cosine similarity in Python
                import numpy as np
                query_vec = np.array(query_embedding)
                
                scored_chunks = []
                for row in rows:
                    try:
                        chunk_embedding = json.loads(row.embedding) if isinstance(row.embedding, str) else row.embedding
                        if not chunk_embedding:
                            continue
                        chunk_vec = np.array(chunk_embedding)
                        
                        # Cosine similarity
                        similarity = np.dot(query_vec, chunk_vec) / (np.linalg.norm(query_vec) * np.linalg.norm(chunk_vec))
                        
                        scored_chunks.append({
                            "id": row.id,
                            "content": row.content,
                            "page_number": row.page_number,
                            "resource_id": row.resource_id,
                            "similarity": float(similarity)
                        })
                    except Exception as chunk_error:
                        logger.warning(f"Error processing chunk {row.id}: {chunk_error}")
                        continue
                
                # Sort by similarity and take top_k
                scored_chunks.sort(key=lambda x: x["similarity"], reverse=True)
                return scored_chunks[:top_k]
                
            except Exception as search_error:
                db.rollback()
                logger.error(f"Error during chunk search: {search_error}")
                return []
            
        except Exception as e:
            db.rollback()
            logger.error(f"Error searching chunks: {e}")
            return []

    async def generate_rag_response(
        self,
        query: str,
        course_id: int,
        course_title: str,
        db: Session,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """
        Generate AI response using RAG - retrieve relevant chunks and generate answer
        """
        try:
            # Search for relevant chunks
            relevant_chunks = self.search_similar_chunks(query, course_id, db, top_k=5)
            
            # Build context from chunks
            if relevant_chunks:
                context_parts = []
                sources = []
                
                for i, chunk in enumerate(relevant_chunks):
                    context_parts.append(f"[Source {i+1}, Page {chunk['page_number']}]:\n{chunk['content']}")
                    sources.append({
                        "page_number": chunk["page_number"],
                        "resource_id": chunk["resource_id"],
                        "similarity": chunk["similarity"]
                    })
                
                context = "\n\n".join(context_parts)
            else:
                context = "No relevant course materials found for this query."
                sources = []
            
            # Build conversation history
            history_text = ""
            if chat_history:
                history_parts = []
                for msg in chat_history[-5:]:  # Last 5 exchanges
                    history_parts.append(f"User: {msg.get('user', '')}")
                    history_parts.append(f"Assistant: {msg.get('assistant', '')}")
                history_text = "\n".join(history_parts)
            
            # Create prompt for Gemini
            prompt = f"""You are an AI learning assistant for the course "{course_title}". 
Your role is to help students understand the course material by answering their questions based on the provided course content.

COURSE CONTEXT (from course materials):
{context}

{f"PREVIOUS CONVERSATION:{chr(10)}{history_text}{chr(10)}" if history_text else ""}

STUDENT QUESTION: {query}

INSTRUCTIONS:
1. Answer the question based primarily on the course context provided above
2. If the context contains relevant information, cite the source (e.g., "According to Page 2...")
3. If the context doesn't contain enough information, acknowledge this and provide general guidance
4. Be helpful, clear, and educational
5. Keep responses concise but thorough
6. If asked about topics not in the course materials, briefly answer but suggest focusing on course content

RESPONSE:"""

            # Generate response using Gemini 2.5 Flash
            response_text = self.generate_content(prompt)
            
            return {
                "response": response_text,
                "sources": sources,
                "chunks_used": len(relevant_chunks)
            }
            
        except Exception as e:
            logger.error(f"Error generating RAG response: {e}")
            return {
                "response": f"I apologize, but I encountered an error processing your question. Please try again. Error: {str(e)}",
                "sources": [],
                "chunks_used": 0
            }

    def get_course_rag_stats(self, course_id: int, db: Session) -> Dict[str, Any]:
        """
        Get RAG statistics for a course (number of chunks, resources processed, etc.)
        """
        try:
            result = db.execute(
                text("""
                    SELECT 
                        COUNT(*) as total_chunks,
                        COUNT(DISTINCT resource_id) as resources_processed,
                        COUNT(DISTINCT page_number) as total_pages
                    FROM document_chunks
                    WHERE course_id = :course_id
                """),
                {"course_id": course_id}
            )
            row = result.fetchone()
            
            return {
                "total_chunks": row.total_chunks if row else 0,
                "resources_processed": row.resources_processed if row else 0,
                "total_pages": row.total_pages if row else 0
            }
        except Exception as e:
            logger.error(f"Error getting RAG stats: {e}")
            return {"total_chunks": 0, "resources_processed": 0, "total_pages": 0}


# Singleton instance
rag_service = RAGService()
