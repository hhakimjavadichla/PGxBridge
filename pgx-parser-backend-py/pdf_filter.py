"""
PDF filtering utilities for keyword-based page extraction.
"""

import io
from typing import List
import pypdf


def find_pages_with_keyword(pdf_bytes: bytes, keyword: str) -> List[int]:
    """
    Find all pages in a PDF that contain the specified keyword (case-insensitive).
    
    Args:
        pdf_bytes: PDF file content as bytes
        keyword: Keyword to search for
        
    Returns:
        List of 1-indexed page numbers containing the keyword
    """
    matched_pages = []
    
    try:
        # Create PDF reader from bytes
        pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        
        # Iterate through all pages
        for page_num, page in enumerate(pdf_reader.pages, start=1):
            # Extract text from page (handle None case)
            text = page.extract_text()
            
            # Perform case-insensitive search
            if text and keyword.lower() in text.lower():
                matched_pages.append(page_num)
                
    except Exception as e:
        # Log error but don't crash - return empty list
        print(f"Error reading PDF: {e}")
        return []
    
    return matched_pages


def build_filtered_pdf(pdf_bytes: bytes, pages: List[int]) -> bytes:
    """
    Create a new PDF containing only the specified pages.
    
    Args:
        pdf_bytes: Original PDF file content as bytes
        pages: List of 1-indexed page numbers to include
        
    Returns:
        New PDF as bytes containing only specified pages
    """
    # Create reader and writer
    pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
    pdf_writer = pypdf.PdfWriter()
    
    # Add specified pages to writer (convert from 1-indexed to 0-indexed)
    for page_num in pages:
        if 0 < page_num <= len(pdf_reader.pages):
            pdf_writer.add_page(pdf_reader.pages[page_num - 1])
    
    # Write to bytes buffer
    output_buffer = io.BytesIO()
    pdf_writer.write(output_buffer)
    output_buffer.seek(0)
    
    return output_buffer.getvalue()