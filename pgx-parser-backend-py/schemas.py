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


class PgxExtractResponse(BaseModel):
    """Response schema for PGX data extraction."""
    meta: Meta
    pgx_genes: List[PgxGeneData]
    extraction_method: str = "azure_layout_parsing"