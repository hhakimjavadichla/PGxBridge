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

from schemas import ProcessResponse, Meta, ErrorResponse, ErrorDetail, PgxExtractResponse, PgxGeneData, PatientInfo, ExtractionResults, SimilarityScores
from pdf_filter import find_pages_with_keyword, build_filtered_pdf
from azure_client import analyze_layout
from pgx_parser import extract_pgx_data, format_pgx_table, PGX_GENES
from patient_parser import extract_patient_info_from_first_page
from llm_parser import extract_patient_info_with_llm, extract_pgx_data_with_llm
from similarity_scorer import compare_patient_info, compare_pgx_genes

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


@app.post("/api/extract-pgx-data", response_model=PgxExtractResponse)
async def extract_pgx_data_endpoint(
    keyword: str = Form(...),
    file: UploadFile = Form(...)
) -> PgxExtractResponse:
    """
    Extract PGX gene data (genotype and metabolizer status) from a PDF report using LLM.
    
    This endpoint:
    1. Extracts text content from the PDF
    2. Uses Azure OpenAI LLM to extract patient info and PGX gene data
    
    Args:
        keyword: Keyword that appears in PGX table pages (used for filtering content)
        file: Uploaded PDF file
        
    Returns:
        PgxExtractResponse with structured gene data and patient info from LLM
    """
    # Read the PDF file
    try:
        pdf_bytes = await file.read()
        logger.info(f"Read PDF file: {len(pdf_bytes)} bytes")
    except Exception as e:
        logger.error(f"Error reading uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "file_read_error",
                "message": "Failed to read uploaded file"
            }}
        )
    
    # Check if Azure OpenAI is configured
    if not os.environ.get("AZURE_OPENAI_API_KEY") or not os.environ.get("AZURE_OPENAI_ENDPOINT"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "configuration_error",
                "message": "Azure OpenAI not configured"
            }}
        )
    
    # Extract text content from PDF
    try:
        from pypdf import PdfReader
        import io
        pdf_reader = PdfReader(io.BytesIO(pdf_bytes))
        
        # Extract first page content for patient info
        first_page_content = pdf_reader.pages[0].extract_text()
        
        # Find pages containing the keyword for PGX data
        matched_pages = find_pages_with_keyword(pdf_bytes, keyword)
        logger.info(f"Found {len(matched_pages)} pages with keyword '{keyword}': {matched_pages}")
        
        # Extract content from matched pages
        filtered_content = ""
        for page_num in matched_pages:
            # Convert to 0-based index
            page_index = page_num - 1
            if page_index < len(pdf_reader.pages):
                filtered_content += pdf_reader.pages[page_index].extract_text() + "\n"
        
        if not filtered_content:
            logger.warning(f"No content found for keyword '{keyword}'")
            # Use all pages if no keyword matches
            filtered_content = "\n".join([page.extract_text() for page in pdf_reader.pages])
        
    except Exception as e:
        logger.error(f"Error extracting PDF content: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "pdf_extraction_error",
                "message": "Failed to extract text from PDF"
            }}
        )
    
    # LLM extraction
    try:
        logger.info("Starting LLM extraction...")
        
        # Extract patient info with LLM
        llm_patient_info = extract_patient_info_with_llm(first_page_content)
        logger.info("Successfully extracted patient information (LLM)")
        
        # Extract PGX data with LLM
        llm_pgx_genes = extract_pgx_data_with_llm(filtered_content)
        logger.info("Successfully extracted PGX data (LLM)")
        
        llm_results = ExtractionResults(
            patient_info=llm_patient_info,
            pgx_genes=llm_pgx_genes,
            extraction_method="azure_openai_llm"
        )
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "llm_extraction_error",
                "message": f"Failed to extract data with LLM: {str(e)}"
            }}
        )
    
    # Create meta information
    meta = Meta(
        original_filename=file.filename,
        keyword=keyword,
        matched_pages=matched_pages,
        matched_pages_count=len(matched_pages)
    )
    
    return PgxExtractResponse(
        meta=meta,
        llm_extraction=llm_results,
        comparison_available=False
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