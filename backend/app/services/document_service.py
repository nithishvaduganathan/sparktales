"""Document processing service for RAG pipeline."""
import os
from typing import List, Optional
from PyPDF2 import PdfReader


def extract_text_from_pdf(file_path: str) -> str:
    """Extract text content from a PDF file."""
    try:
        reader = PdfReader(file_path)
        text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
        return text.strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def extract_text_from_txt(file_path: str) -> str:
    """Extract text content from a TXT file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        return f"Error extracting text: {str(e)}"


def extract_text(file_path: str, file_type: str) -> str:
    """Extract text from a file based on its type."""
    if file_type.lower() == '.pdf':
        return extract_text_from_pdf(file_path)
    elif file_type.lower() == '.txt':
        return extract_text_from_txt(file_path)
    else:
        return ""


def chunk_text(text: str, chunk_size: int = 1000, chunk_overlap: int = 200) -> List[str]:
    """Split text into overlapping chunks for embedding."""
    if not text:
        return []
    
    chunks = []
    start = 0
    text_length = len(text)
    
    while start < text_length:
        end = start + chunk_size
        chunk = text[start:end]
        chunks.append(chunk)
        start = end - chunk_overlap
        
        if start >= text_length:
            break
    
    return chunks
