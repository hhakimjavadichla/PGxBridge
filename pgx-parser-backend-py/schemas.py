"""
Pydantic schemas for API request/response models.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel


class Meta(BaseModel):
    """Metadata about the processed document."""
    original_filename: str
    keyword: str
    matched_pages: List[int]
    matched_pages_count: int
    filtered_pdf_page_count: Optional[int] = None
    azure_model_id: Optional[str] = None
    azure_api_version: Optional[str] = None


class ProcessResponse(BaseModel):
    """Response schema for document processing endpoint."""
    meta: Meta
    azure_result: Optional[Dict[str, Any]]
    message: Optional[str] = None


class ErrorDetail(BaseModel):
    """Error detail schema."""
    type: str
    message: str


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: ErrorDetail


class PgxGeneData(BaseModel):
    """PGX gene information."""
    gene: str
    genotype: str
    metabolizer_status: str


class PatientInfo(BaseModel):
    """Patient information from first page tables."""
    # Table 1 fields
    patient_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    test: Optional[str] = None
    report_date: Optional[str] = None
    report_id: Optional[str] = None
    
    # Table 2 fields
    cohort: Optional[str] = None
    sample_type: Optional[str] = None
    sample_collection_date: Optional[str] = None
    sample_received_date: Optional[str] = None
    processed_date: Optional[str] = None
    ordering_clinician: Optional[str] = None
    npi: Optional[str] = None
    indication_for_testing: Optional[str] = None


class ExtractionResults(BaseModel):
    """Combined extraction results from both methods."""
    patient_info: PatientInfo
    pgx_genes: List[PgxGeneData]
    extraction_method: str


class PgxExtractResponse(BaseModel):
    """Response schema for PGX data extraction with both methods."""
    meta: Meta
    document_intelligence: ExtractionResults
    llm_extraction: Optional[ExtractionResults] = None
    comparison_available: bool = False