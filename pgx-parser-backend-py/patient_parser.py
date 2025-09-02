"""
Patient information parsing utilities to extract data from the first page of PDF reports.
"""

import re
from typing import Dict, Optional
import logging
from schemas import PatientInfo

logger = logging.getLogger(__name__)

# Field mapping for patient information
PATIENT_FIELDS = {
    # Table 1 fields
    "patient_name": ["Patient Name", "Name", "Patient"],
    "date_of_birth": ["Date of Birth", "DOB", "Birth Date"],
    "test": ["Test", "Test Type", "Assay"],
    "report_date": ["Report Date", "Date", "Reported"],
    "report_id": ["Report ID", "ID", "Report Number"],
    
    # Table 2 fields
    "cohort": ["Cohort", "Population"],
    "sample_type": ["Sample Type", "Specimen Type", "Sample"],
    "sample_collection_date": ["Sample Collection Date", "Collection Date", "Collected"],
    "sample_received_date": ["Sample Received Date", "Received Date", "Received"],
    "processed_date": ["Processed Date", "Processing Date", "Processed"],
    "ordering_clinician": ["Ordering Clinician", "Clinician", "Physician", "Doctor"],
    "npi": ["NPI", "NPI Number"],
    "indication_for_testing": ["Indication for Testing", "Indication", "Testing Indication"]
}


def extract_patient_info_from_content(content: str) -> PatientInfo:
    """
    Extract patient information from the first page content.
    
    Args:
        content: Text content from the first page of the PDF
        
    Returns:
        PatientInfo object with extracted data
    """
    patient_data = {}
    
    if not content:
        logger.warning("No content provided for patient info parsing")
        return PatientInfo()
    
    # Clean up content - normalize whitespace but preserve line breaks for table structure
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n\s*\n', '\n', content)
    
    # Extract each field using multiple patterns
    for field_key, field_variations in PATIENT_FIELDS.items():
        value = extract_field_value(content, field_variations)
        if value:
            patient_data[field_key] = value
            logger.info(f"Found {field_key}: {value}")
    
    return PatientInfo(**patient_data)


def extract_field_value(content: str, field_names: list) -> Optional[str]:
    """
    Extract a field value using multiple possible field name variations.
    
    Args:
        content: Text content to search
        field_names: List of possible field name variations
        
    Returns:
        Extracted field value or None if not found
    """
    for field_name in field_names:
        # Try multiple patterns to handle different table formats
        patterns = [
            # Pattern 1: Field name followed by colon and value on same line
            rf"{re.escape(field_name)}\s*:?\s*([^\n\r]+)",
            
            # Pattern 2: Field name on one line, value on next line
            rf"{re.escape(field_name)}\s*:?\s*\n\s*([^\n\r]+)",
            
            # Pattern 3: Field name and value separated by whitespace (table format)
            rf"{re.escape(field_name)}\s+([^\n\r\t]+?)(?:\s{{2,}}|\t|\n|$)",
            
            # Pattern 4: Field name in a cell, value in adjacent cell (table format)
            rf"{re.escape(field_name)}\s*(?:\||\t)\s*([^\n\r\|]+)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE | re.MULTILINE)
            if match:
                value = match.group(1).strip()
                # Clean up the value
                value = re.sub(r'\s+', ' ', value)
                value = value.strip('|').strip()
                
                # Skip if value is empty or just punctuation
                if value and not re.match(r'^[\s\-_|:]+$', value):
                    return value
    
    return None


def extract_patient_info_from_first_page(pdf_bytes: bytes) -> PatientInfo:
    """
    Extract patient information specifically from the first page of a PDF.
    
    Args:
        pdf_bytes: PDF file content as bytes
        
    Returns:
        PatientInfo object with extracted data
    """
    try:
        import pypdf
        import io
        
        # Create PDF reader and extract first page only
        pdf_reader = pypdf.PdfReader(io.BytesIO(pdf_bytes))
        
        if len(pdf_reader.pages) == 0:
            logger.warning("PDF has no pages")
            return PatientInfo()
        
        # Extract text from first page
        first_page = pdf_reader.pages[0]
        content = first_page.extract_text()
        
        if not content:
            logger.warning("No text extracted from first page")
            return PatientInfo()
        
        logger.info("Extracting patient information from first page")
        return extract_patient_info_from_content(content)
        
    except Exception as e:
        logger.error(f"Error extracting patient info from first page: {e}")
        return PatientInfo()


def extract_patient_info_from_azure_result(azure_result: Dict) -> PatientInfo:
    """
    Extract patient information from Azure Document Intelligence results.
    This assumes the Azure result includes the first page content.
    
    Args:
        azure_result: Azure Document Intelligence analysis result
        
    Returns:
        PatientInfo object with extracted data
    """
    try:
        # Extract content from Azure result
        content = azure_result.get("content", "")
        
        # For better accuracy, try to extract just the first page content
        # Azure results include page information
        pages = azure_result.get("pages", [])
        if pages and len(pages) > 0:
            # Get content from first page only
            first_page_content = ""
            
            # Extract paragraphs from first page
            paragraphs = azure_result.get("paragraphs", [])
            for paragraph in paragraphs:
                bounding_regions = paragraph.get("bounding_regions", [])
                for region in bounding_regions:
                    if region.get("page_number", 1) == 1:  # First page
                        first_page_content += paragraph.get("content", "") + "\n"
            
            if first_page_content:
                content = first_page_content
        
        return extract_patient_info_from_content(content)
        
    except Exception as e:
        logger.error(f"Error parsing patient info from Azure result: {e}")
        return PatientInfo()
