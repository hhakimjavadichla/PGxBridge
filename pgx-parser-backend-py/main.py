"""
FastAPI backend for PDF processing with Azure Document Intelligence.
"""

import os
import logging
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from azure.core.exceptions import AzureError
from dotenv import load_dotenv

from schemas import ProcessResponse, Meta, ErrorResponse, ErrorDetail
from pdf_filter import find_pages_with_keyword, build_filtered_pdf
from azure_client import analyze_layout

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="PGX Parser Backend",
    description="PDF processing with Azure Document Intelligence",
    version="1.0.0"
)

# Configure CORS
allowed_origins = os.environ.get("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Constants
MAX_FILE_SIZE_MB = 520  # Leave headroom under Azure's 500MB limit
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024


@app.get("/healthz")
async def health_check() -> Dict[str, bool]:
    """Health check endpoint."""
    return {"ok": True}


@app.post("/api/process-document", response_model=ProcessResponse)
async def process_document(
    keyword: str = Form(...),
    file: UploadFile = Form(...)
) -> ProcessResponse:
    """
    Process a PDF document by filtering pages containing a keyword
    and analyzing with Azure Document Intelligence.
    
    Args:
        keyword: Keyword to search for in the PDF
        file: Uploaded PDF file
        
    Returns:
        ProcessResponse with metadata and Azure analysis results
    """
    # Validate file type
    if not file.content_type or "pdf" not in file.content_type.lower():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "invalid_file_type",
                "message": f"File must be PDF. Received: {file.content_type or 'unknown'}"
            }}
        )
    
    # Read file content
    try:
        pdf_bytes = await file.read()
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "file_read_error",
                "message": "Failed to read uploaded file"
            }}
        )
    
    # Check file size
    file_size_mb = len(pdf_bytes) / (1024 * 1024)
    if len(pdf_bytes) > MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail={"error": {
                "type": "file_too_large",
                "message": f"File size ({file_size_mb:.1f}MB) exceeds maximum allowed size ({MAX_FILE_SIZE_MB}MB)"
            }}
        )
    
    # Find pages containing keyword
    try:
        matched_pages = find_pages_with_keyword(pdf_bytes, keyword)
        logger.info(f"Found {len(matched_pages)} pages with keyword '{keyword}': {matched_pages}")
    except Exception as e:
        logger.error(f"Error searching PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "pdf_search_error",
                "message": "Failed to search PDF content"
            }}
        )
    
    # If no matches found, return early without calling Azure
    if not matched_pages:
        return ProcessResponse(
            meta=Meta(
                original_filename=file.filename,
                keyword=keyword,
                matched_pages=[],
                matched_pages_count=0
            ),
            azure_result=None,
            message="No pages contained the keyword."
        )
    
    # Build filtered PDF with only matched pages
    try:
        filtered_pdf_bytes = build_filtered_pdf(pdf_bytes, matched_pages)
    except Exception as e:
        logger.error(f"Error building filtered PDF: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "pdf_filter_error",
                "message": "Failed to create filtered PDF"
            }}
        )
    
    # Analyze with Azure Document Intelligence
    try:
        azure_result = analyze_layout(filtered_pdf_bytes)
        
        # Extract model info from result
        model_id = azure_result.get("model_id", "prebuilt-layout")
        api_version = azure_result.get("api_version", "unknown")
        
        # Log operation ID if available
        if "operation_id" in azure_result:
            logger.info(f"Azure operation ID: {azure_result['operation_id']}")
        
    except AzureError as e:
        logger.error(f"Azure API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail={"error": {
                "type": "azure_api_error",
                "message": f"Azure Document Intelligence error: {str(e)}"
            }}
        )
    except Exception as e:
        logger.error(f"Unexpected error calling Azure: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "azure_call_error",
                "message": "Failed to analyze document with Azure"
            }}
        )
    
    # Return successful response
    return ProcessResponse(
        meta=Meta(
            original_filename=file.filename,
            keyword=keyword,
            matched_pages=matched_pages,
            matched_pages_count=len(matched_pages),
            filtered_pdf_page_count=len(matched_pages),
            azure_model_id=model_id,
            azure_api_version=api_version
        ),
        azure_result=azure_result
    )


# Custom exception handler for better error responses
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Ensure all HTTP exceptions return proper JSON error format."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail
        )
    else:
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": {
                "type": "http_error",
                "message": str(exc.detail)
            }}
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)