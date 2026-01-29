"""
FastAPI backend for PDF processing with Azure Document Intelligence.
"""

import os
import io
import zipfile
import logging
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, UploadFile, Form, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, Response
from azure.core.exceptions import AzureError
from dotenv import load_dotenv

from schemas import ProcessResponse, Meta, ErrorResponse, ErrorDetail, PgxExtractResponse, PgxGeneData, PatientInfo, ExtractionResults, SimilarityScores, CPICSummary
from pdf_filter import find_pages_with_keyword, build_filtered_pdf
from azure_client import analyze_layout
from pgx_parser import extract_pgx_data, format_pgx_table, PGX_GENES
from patient_parser import extract_patient_info_from_first_page
from llm_parser import extract_patient_info_with_llm, extract_pgx_data_with_llm
from similarity_scorer import compare_patient_info, compare_pgx_genes
from cpic_annotator import get_cpic_annotator
from report_generator import generate_patient_report, generate_patient_report_filename, generate_patient_report_docxtpl, generate_ehr_report, generate_ehr_report_filename, generate_ehr_report_docxtpl
from feedback_manager import get_feedback_manager, FeedbackCategory, FeedbackStatus
from auth_manager import get_auth_manager, UserRole

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


# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

def get_current_user(authorization: str = None) -> Optional[Dict]:
    """
    Extract and validate token from Authorization header.
    Returns user info if valid, None otherwise.
    """
    if not authorization:
        return None
    
    # Expect "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        return None
    
    token = parts[1]
    auth_mgr = get_auth_manager()
    return auth_mgr.validate_token(token)


def require_auth(authorization: str = None) -> Dict:
    """Dependency that requires valid authentication."""
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"type": "unauthorized", "message": "Invalid or missing authentication token"}}
        )
    return user


def require_admin(authorization: str = None) -> Dict:
    """Dependency that requires admin authentication."""
    user = require_auth(authorization)
    if user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"type": "forbidden", "message": "Admin access required"}}
        )
    return user


@app.post("/api/auth/login")
async def login(
    username: str = Form(...),
    password: str = Form(...)
) -> Dict[str, Any]:
    """
    Authenticate user and return a token.
    """
    auth_mgr = get_auth_manager()
    result = auth_mgr.authenticate(username, password)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"type": "invalid_credentials", "message": "Invalid username or password"}}
        )
    
    return result


@app.post("/api/auth/logout")
async def logout(
    authorization: str = Form(None)
) -> Dict[str, Any]:
    """
    Invalidate the current token.
    """
    if not authorization:
        return {"success": True, "message": "No token provided"}
    
    parts = authorization.split()
    if len(parts) == 2 and parts[0].lower() == "bearer":
        token = parts[1]
    else:
        token = authorization
    
    auth_mgr = get_auth_manager()
    auth_mgr.logout(token)
    
    return {"success": True, "message": "Logged out successfully"}


@app.get("/api/auth/validate")
async def validate_token(
    authorization: str = None
) -> Dict[str, Any]:
    """
    Validate the current token and return user info.
    """
    user = get_current_user(authorization)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"error": {"type": "invalid_token", "message": "Invalid or expired token"}}
        )
    
    return {"valid": True, "user": user}


@app.get("/api/auth/users")
async def list_users(
    authorization: str = None
) -> Dict[str, Any]:
    """
    List all users (admin only).
    """
    require_admin(authorization)
    
    auth_mgr = get_auth_manager()
    users = auth_mgr.list_users()
    
    return {"users": users}


@app.post("/api/auth/users")
async def create_user(
    username: str = Form(...),
    password: str = Form(...),
    role: str = Form("user"),
    authorization: str = Form(None)
) -> Dict[str, Any]:
    """
    Create a new user (admin only).
    """
    admin = require_admin(authorization)
    
    auth_mgr = get_auth_manager()
    result = auth_mgr.create_user(
        username=username,
        password=password,
        role=role,
        created_by=admin.get("username", "admin")
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"type": "user_creation_failed", "message": result.get("message")}}
        )
    
    return result


@app.delete("/api/auth/users/{username}")
async def delete_user(
    username: str,
    authorization: str = None
) -> Dict[str, Any]:
    """
    Delete a user (admin only).
    """
    admin = require_admin(authorization)
    
    auth_mgr = get_auth_manager()
    result = auth_mgr.delete_user(username, deleted_by=admin.get("username", "admin"))
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"type": "user_deletion_failed", "message": result.get("message")}}
        )
    
    return result


@app.put("/api/auth/users/{username}/password")
async def update_user_password(
    username: str,
    new_password: str = Form(...),
    authorization: str = Form(None)
) -> Dict[str, Any]:
    """
    Update a user's password (admin or self).
    """
    user = require_auth(authorization)
    
    # Users can update their own password, admins can update anyone's
    if user.get("username") != username and user.get("role") != UserRole.ADMIN.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": {"type": "forbidden", "message": "Cannot update other users' passwords"}}
        )
    
    auth_mgr = get_auth_manager()
    result = auth_mgr.update_password(
        username=username,
        new_password=new_password,
        updated_by=user.get("username", "unknown")
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"type": "password_update_failed", "message": result.get("message")}}
        )
    
    return result


@app.put("/api/auth/users/{username}/toggle")
async def toggle_user_status(
    username: str,
    active: bool = Form(...),
    authorization: str = Form(None)
) -> Dict[str, Any]:
    """
    Enable or disable a user (admin only).
    """
    admin = require_admin(authorization)
    
    auth_mgr = get_auth_manager()
    result = auth_mgr.toggle_user_active(
        username=username,
        active=active,
        updated_by=admin.get("username", "admin")
    )
    
    if not result.get("success"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {"type": "toggle_failed", "message": result.get("message")}}
        )
    
    return result


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
        
        # Annotate with CPIC data
        logger.info("Annotating PGX data with CPIC standards...")
        cpic_annotator = get_cpic_annotator()
        
        # Convert PgxGeneData objects to dicts for annotation
        genes_dict = [
            {
                'gene': g.gene,
                'genotype': g.genotype,
                'metabolizer_status': g.metabolizer_status
            }
            for g in llm_pgx_genes
        ]
        
        # Annotate genes
        annotated_genes_dict = cpic_annotator.annotate_genes(genes_dict)
        
        # Convert back to PgxGeneData objects with CPIC fields
        annotated_genes = [PgxGeneData(**g) for g in annotated_genes_dict]
        
        # Get summary statistics
        cpic_stats = cpic_annotator.get_summary_statistics(annotated_genes_dict)
        cpic_summary = CPICSummary(**cpic_stats)
        
        logger.info(f"CPIC annotation complete: {cpic_stats['cpic_found']}/{cpic_stats['total_genes']} genes found, {cpic_stats['high_risk_count']} high-risk")
        
        llm_results = ExtractionResults(
            patient_info=llm_patient_info,
            pgx_genes=annotated_genes,
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
        comparison_available=False,
        cpic_summary=cpic_summary
    )


@app.post("/api/generate-patient-report")
async def generate_patient_report_endpoint(
    keyword: str = Form(...),
    file: UploadFile = Form(...)
) -> Response:
    """
    Generate a patient-facing Word document report from a PDF.
    
    This endpoint:
    1. Extracts patient info and PGX gene data from the PDF
    2. Generates a Word document using the patient report template
    3. Returns the Word document as a downloadable file
    
    Table 1: High-risk variants + all CYP2C19 results
    Table 2: All PGX results
    
    Args:
        keyword: Keyword that appears in PGX table pages
        file: Uploaded PDF file
        
    Returns:
        Word document (.docx) file
    """
    # Read the PDF file
    try:
        pdf_bytes = await file.read()
        logger.info(f"Read PDF file for report generation: {len(pdf_bytes)} bytes")
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
        logger.info(f"Found {len(matched_pages)} pages with keyword '{keyword}'")
        
        # Extract content from matched pages
        filtered_content = ""
        for page_num in matched_pages:
            page_index = page_num - 1
            if page_index < len(pdf_reader.pages):
                filtered_content += pdf_reader.pages[page_index].extract_text() + "\n"
        
        if not filtered_content:
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
        logger.info("Extracting data with LLM for report generation...")
        
        # Extract patient info with LLM
        llm_patient_info = extract_patient_info_with_llm(first_page_content)
        
        # Extract PGX data with LLM
        llm_pgx_genes = extract_pgx_data_with_llm(filtered_content)
        
        # Annotate with CPIC data
        cpic_annotator = get_cpic_annotator()
        genes_dict = [
            {
                'gene': g.gene,
                'genotype': g.genotype,
                'metabolizer_status': g.metabolizer_status
            }
            for g in llm_pgx_genes
        ]
        annotated_genes_dict = cpic_annotator.annotate_genes(genes_dict)
        
        logger.info(f"Extracted {len(annotated_genes_dict)} genes with CPIC annotations")
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "llm_extraction_error",
                "message": f"Failed to extract data with LLM: {str(e)}"
            }}
        )
    
    # Generate Word document
    try:
        patient_info_dict = {
            'patient_name': llm_patient_info.patient_name,
            'date_of_birth': llm_patient_info.date_of_birth,
            'report_date': llm_patient_info.report_date,
            'report_id': llm_patient_info.report_id,
        }
        
        doc_bytes = generate_patient_report_docxtpl(patient_info_dict, annotated_genes_dict)
        filename = generate_patient_report_filename(patient_info_dict)
        
        logger.info(f"Generated patient report: {filename}")
        
        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except FileNotFoundError as e:
        logger.error(f"Template not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "template_not_found",
                "message": str(e)
            }}
        )
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "report_generation_error",
                "message": f"Failed to generate Word document: {str(e)}"
            }}
        )


@app.post("/api/generate-ehr-report")
async def generate_ehr_report_endpoint(
    keyword: str = Form(...),
    file: UploadFile = Form(...)
) -> Response:
    """
    Generate an EHR-facing Word document report from a PDF.
    
    This endpoint:
    1. Extracts patient info and PGX gene data from the PDF
    2. Generates a Word document using the EHR note template
    3. Returns the Word document as a downloadable file
    
    Table 1: High-risk variants + all CYP2C19 results (Priority)
    Table 2: Normal/routine/low risk results (Standard)
    Table 3: Unknown/indeterminate priority results (Unknown)
    
    Args:
        keyword: Keyword that appears in PGX table pages
        file: Uploaded PDF file
        
    Returns:
        Word document (.docx) file
    """
    # Read the PDF file
    try:
        pdf_bytes = await file.read()
        logger.info(f"Read PDF file for EHR report generation: {len(pdf_bytes)} bytes")
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
        logger.info(f"Found {len(matched_pages)} pages with keyword '{keyword}'")
        
        # Extract content from matched pages
        filtered_content = ""
        for page_num in matched_pages:
            page_index = page_num - 1
            if page_index < len(pdf_reader.pages):
                filtered_content += pdf_reader.pages[page_index].extract_text() + "\n"
        
        if not filtered_content:
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
        logger.info("Extracting data with LLM for EHR report generation...")
        
        # Extract patient info with LLM
        llm_patient_info = extract_patient_info_with_llm(first_page_content)
        
        # Extract PGX data with LLM
        llm_pgx_genes = extract_pgx_data_with_llm(filtered_content)
        
        # Annotate with CPIC data
        cpic_annotator = get_cpic_annotator()
        genes_dict = [
            {
                'gene': g.gene,
                'genotype': g.genotype,
                'metabolizer_status': g.metabolizer_status
            }
            for g in llm_pgx_genes
        ]
        annotated_genes_dict = cpic_annotator.annotate_genes(genes_dict)
        
        logger.info(f"Extracted {len(annotated_genes_dict)} genes with CPIC annotations for EHR report")
        
    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "llm_extraction_error",
                "message": f"Failed to extract data with LLM: {str(e)}"
            }}
        )
    
    # Generate EHR Word document
    try:
        patient_info_dict = {
            'patient_name': llm_patient_info.patient_name,
            'date_of_birth': llm_patient_info.date_of_birth,
            'report_date': llm_patient_info.report_date,
            'report_id': llm_patient_info.report_id,
        }
        
        doc_bytes = generate_ehr_report_docxtpl(patient_info_dict, annotated_genes_dict)
        filename = generate_ehr_report_filename(patient_info_dict)
        
        logger.info(f"Generated EHR report: {filename}")
        
        return Response(
            content=doc_bytes,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"'
            }
        )
        
    except FileNotFoundError as e:
        logger.error(f"EHR template not found: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "template_not_found",
                "message": str(e)
            }}
        )
    except Exception as e:
        logger.error(f"Error generating EHR report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "report_generation_error",
                "message": f"Failed to generate EHR Word document: {str(e)}"
            }}
        )


# ============================================================================
# BATCH REPORT GENERATION ENDPOINTS
# ============================================================================

@app.post("/api/generate-batch-patient-reports")
async def generate_batch_patient_reports(
    results_json: str = Form(...)
):
    """
    Generate patient-facing Word documents for multiple processed results.
    Returns a ZIP file containing all generated documents.
    
    Args:
        results_json: JSON string containing array of processed results
        
    Returns:
        ZIP file containing all generated Word documents
    """
    import json
    
    try:
        results = json.loads(results_json)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "invalid_json",
                "message": f"Invalid JSON data: {str(e)}"
            }}
        )
    
    if not isinstance(results, list) or len(results) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "invalid_data",
                "message": "Results must be a non-empty array"
            }}
        )
    
    try:
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            generated_count = 0
            
            for result in results:
                # Skip failed results
                if not result.get('success', False):
                    continue
                
                data = result.get('data', {})
                llm_extraction = data.get('llm_extraction', {})
                patient_info = llm_extraction.get('patient_info', {})
                pgx_genes = llm_extraction.get('pgx_genes', [])
                
                if not patient_info or not pgx_genes:
                    continue
                
                # Generate the Word document
                doc_bytes = generate_patient_report_docxtpl(patient_info, pgx_genes)
                
                # Create filename
                patient_name = patient_info.get('patient_name', 'Unknown')
                safe_name = ''.join(c for c in patient_name if c.isalnum() or c in ' -_').strip()
                safe_name = safe_name.replace(' ', '_') or 'Patient'
                filename = f"PGx_Report_{safe_name}.docx"
                
                # Handle duplicate filenames
                base_name = filename[:-5]  # Remove .docx
                counter = 1
                while filename in [info.filename for info in zip_file.filelist]:
                    filename = f"{base_name}_{counter}.docx"
                    counter += 1
                
                zip_file.writestr(filename, doc_bytes)
                generated_count += 1
        
        if generated_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {
                    "type": "no_reports",
                    "message": "No valid results to generate reports from"
                }}
            )
        
        zip_buffer.seek(0)
        
        from datetime import datetime
        zip_filename = f"PGx_Patient_Reports_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating batch patient reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "batch_generation_error",
                "message": f"Failed to generate batch reports: {str(e)}"
            }}
        )


@app.post("/api/generate-batch-ehr-reports")
async def generate_batch_ehr_reports(
    results_json: str = Form(...)
):
    """
    Generate EHR-facing Word documents for multiple processed results.
    Returns a ZIP file containing all generated documents.
    
    Args:
        results_json: JSON string containing array of processed results
        
    Returns:
        ZIP file containing all generated Word documents
    """
    import json
    
    try:
        results = json.loads(results_json)
    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "invalid_json",
                "message": f"Invalid JSON data: {str(e)}"
            }}
        )
    
    if not isinstance(results, list) or len(results) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "invalid_data",
                "message": "Results must be a non-empty array"
            }}
        )
    
    try:
        # Create ZIP file in memory
        zip_buffer = io.BytesIO()
        
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            generated_count = 0
            
            for result in results:
                # Skip failed results
                if not result.get('success', False):
                    continue
                
                data = result.get('data', {})
                llm_extraction = data.get('llm_extraction', {})
                patient_info = llm_extraction.get('patient_info', {})
                pgx_genes = llm_extraction.get('pgx_genes', [])
                
                if not patient_info or not pgx_genes:
                    continue
                
                # Generate the Word document
                doc_bytes = generate_ehr_report_docxtpl(patient_info, pgx_genes)
                
                # Create filename
                patient_name = patient_info.get('patient_name', 'Unknown')
                safe_name = ''.join(c for c in patient_name if c.isalnum() or c in ' -_').strip()
                safe_name = safe_name.replace(' ', '_') or 'Patient'
                filename = f"PGx_EHR_Note_{safe_name}.docx"
                
                # Handle duplicate filenames
                base_name = filename[:-5]  # Remove .docx
                counter = 1
                while filename in [info.filename for info in zip_file.filelist]:
                    filename = f"{base_name}_{counter}.docx"
                    counter += 1
                
                zip_file.writestr(filename, doc_bytes)
                generated_count += 1
        
        if generated_count == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": {
                    "type": "no_reports",
                    "message": "No valid results to generate reports from"
                }}
            )
        
        zip_buffer.seek(0)
        
        from datetime import datetime
        zip_filename = f"PGx_EHR_Notes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
        
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={
                "Content-Disposition": f"attachment; filename={zip_filename}"
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating batch EHR reports: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "batch_generation_error",
                "message": f"Failed to generate batch EHR reports: {str(e)}"
            }}
        )


# ============================================================================
# FEEDBACK ENDPOINTS
# ============================================================================

@app.post("/api/feedback/submit")
async def submit_feedback(
    category: str = Form(...),
    description: str = Form(...),
    gene: str = Form(None),
    genotype_reported: str = Form(None),
    genotype_expected: str = Form(None),
    phenotype_reported: str = Form(None),
    phenotype_expected: str = Form(None),
    patient_id: str = Form(None),
    filename: str = Form(None)
) -> Dict[str, Any]:
    """
    Submit feedback about parsing, annotation, or export issues.
    
    Args:
        category: Issue type (parsing_error, annotation_error, export_error, other)
        description: Description of the issue
        gene: Gene name (if applicable)
        genotype_reported: Genotype extracted from PDF
        genotype_expected: What the genotype should be
        phenotype_reported: Phenotype from CPIC or PDF
        phenotype_expected: What the phenotype should be
        patient_id: Anonymized patient identifier
        filename: Source PDF filename
        
    Returns:
        Confirmation with feedback ID
    """
    # Validate category
    valid_categories = [c.value for c in FeedbackCategory]
    if category not in valid_categories:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "invalid_category",
                "message": f"Category must be one of: {valid_categories}"
            }}
        )
    
    try:
        feedback_mgr = get_feedback_manager()
        result = feedback_mgr.submit_feedback(
            category=category,
            description=description,
            gene=gene,
            genotype_reported=genotype_reported,
            genotype_expected=genotype_expected,
            phenotype_reported=phenotype_reported,
            phenotype_expected=phenotype_expected,
            patient_id=patient_id,
            filename=filename
        )
        return result
    except Exception as e:
        logger.error(f"Error submitting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "feedback_submission_error",
                "message": f"Failed to submit feedback: {str(e)}"
            }}
        )


@app.get("/api/feedback/list")
async def list_feedback(
    category: str = None,
    status_filter: str = None,
    gene: str = None
) -> Dict[str, Any]:
    """
    List all feedback items, optionally filtered.
    
    Args:
        category: Filter by category
        status_filter: Filter by status (pending, in_review, resolved, rejected)
        gene: Filter by gene name
        
    Returns:
        List of feedback items
    """
    try:
        feedback_mgr = get_feedback_manager()
        items = feedback_mgr.get_all_feedback(
            category=category,
            status=status_filter,
            gene=gene
        )
        return {"feedback_items": items, "count": len(items)}
    except Exception as e:
        logger.error(f"Error listing feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "feedback_list_error",
                "message": f"Failed to list feedback: {str(e)}"
            }}
        )


@app.get("/api/feedback/summary")
async def get_feedback_summary() -> Dict[str, Any]:
    """
    Get summary statistics of all feedback.
    
    Returns:
        Summary with counts by category, status, and gene
    """
    try:
        feedback_mgr = get_feedback_manager()
        return feedback_mgr.get_summary()
    except Exception as e:
        logger.error(f"Error getting feedback summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "feedback_summary_error",
                "message": f"Failed to get feedback summary: {str(e)}"
            }}
        )


@app.get("/api/feedback/{feedback_id}")
async def get_feedback(feedback_id: str) -> Dict[str, Any]:
    """
    Get a specific feedback item by ID.
    
    Args:
        feedback_id: The feedback ID
        
    Returns:
        Feedback item details
    """
    try:
        feedback_mgr = get_feedback_manager()
        item = feedback_mgr.get_feedback_by_id(feedback_id)
        if item is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {
                    "type": "feedback_not_found",
                    "message": f"Feedback with ID {feedback_id} not found"
                }}
            )
        return item
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "feedback_get_error",
                "message": f"Failed to get feedback: {str(e)}"
            }}
        )


@app.put("/api/feedback/{feedback_id}/status")
async def update_feedback_status(
    feedback_id: str,
    new_status: str = Form(...),
    resolution_notes: str = Form(None)
) -> Dict[str, Any]:
    """
    Update the status of a feedback item.
    
    Args:
        feedback_id: The feedback ID
        new_status: New status (pending, in_review, resolved, rejected)
        resolution_notes: Notes about the resolution
        
    Returns:
        Update confirmation
    """
    # Validate status
    valid_statuses = [s.value for s in FeedbackStatus]
    if new_status not in valid_statuses:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": {
                "type": "invalid_status",
                "message": f"Status must be one of: {valid_statuses}"
            }}
        )
    
    try:
        feedback_mgr = get_feedback_manager()
        result = feedback_mgr.update_feedback_status(
            feedback_id=feedback_id,
            new_status=new_status,
            resolution_notes=resolution_notes
        )
        if not result.get("success"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": {
                    "type": "feedback_not_found",
                    "message": result.get("message")
                }}
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating feedback status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "feedback_update_error",
                "message": f"Failed to update feedback: {str(e)}"
            }}
        )


@app.get("/api/feedback/export/csv")
async def export_feedback_csv():
    """
    Export all feedback to CSV format.
    
    Returns:
        CSV file download
    """
    try:
        feedback_mgr = get_feedback_manager()
        csv_content = feedback_mgr.export_feedback_csv()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=pgx_feedback_export.csv"
            }
        )
    except Exception as e:
        logger.error(f"Error exporting feedback: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"error": {
                "type": "feedback_export_error",
                "message": f"Failed to export feedback: {str(e)}"
            }}
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