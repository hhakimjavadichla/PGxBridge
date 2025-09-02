"""
PGX-specific parsing utilities to extract genotype and metabolizer status from Azure results.
"""

import re
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

# Standard PGX genes to look for
PGX_GENES = [
    "CYP2B6",
    "CYP2C19", 
    "CYP2C9",
    "CYP2D6",
    "CYP3A5",
    "CYP4F2",
    "DPYD",
    "NAT2",
    "NUDT15",
    "SLCO1B1",
    "TPMT",
    "UGT1A1",
    "VKORC1"
]


def extract_pgx_data_from_content(content: str) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Extract genotype and metabolizer status for each PGX gene from text content.
    
    This function handles various table formats that might appear in PGX reports:
    - Standard tables with Gene | Genotype | Metabolizer Status columns
    - Tables where data appears in subsequent lines
    - Tables with varying spacing and formatting
    
    Args:
        content: Text content extracted from PDF pages
        
    Returns:
        Dictionary mapping gene names to their genotype and metabolizer status
    """
    # Initialize result with all genes
    pgx_data = {
        gene: {
            "genotype": None,
            "metabolizer_status": None
        }
        for gene in PGX_GENES
    }
    
    if not content:
        logger.warning("No content provided for parsing")
        return pgx_data
    
    # Clean up content - normalize whitespace
    content = re.sub(r'\s+', ' ', content)
    
    # Method 1: Look for each gene and its associated data
    for gene in PGX_GENES:
        # Try multiple regex patterns to capture different table formats
        patterns = [
            # Pattern 1: Gene followed by genotype and metabolizer status on same line
            rf"{gene}\s+([*\w/\-\(\)\.]+)\s+([\w\s]*(?:Metabolizer|Function|Indeterminate))",
            
            # Pattern 2: Gene with genotype containing special characters
            rf"{gene}\s+([*\d/\(\)A-Za-z\.\-:]+)\s+([\w\s]*(?:Metabolizer|Function|Indeterminate))",
            
            # Pattern 3: More flexible pattern for complex genotypes
            rf"{gene}\s+([^\s]+(?:\s*[^\s]+)*?)\s+(Normal|Intermediate|Poor|Rapid|Ultra[- ]?rapid)?\s*(?:Metabolizer|Function)",
            
            # Pattern 4: Handle cases where status comes before "Metabolizer/Function"
            rf"{gene}\s+([*\w/\-\(\)\.]+)\s+(Normal|Intermediate|Poor|Rapid|Ultra[- ]?rapid|Indeterminate)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                genotype = match.group(1).strip()
                metabolizer = match.group(2).strip() if len(match.groups()) > 1 else None
                
                # Clean up the metabolizer status
                if metabolizer:
                    # Add "Metabolizer" if it's just the status
                    if metabolizer in ["Normal", "Intermediate", "Poor", "Rapid", "Ultra-rapid"]:
                        metabolizer = f"{metabolizer} Metabolizer"
                    elif not any(word in metabolizer for word in ["Metabolizer", "Function", "Indeterminate"]):
                        metabolizer = f"{metabolizer} Metabolizer"
                
                pgx_data[gene] = {
                    "genotype": genotype,
                    "metabolizer_status": metabolizer or "Not specified"
                }
                logger.info(f"Found {gene}: genotype={genotype}, status={metabolizer}")
                break
    
    # Method 2: If first method didn't find all genes, try parsing as a structured table
    missing_genes = [gene for gene in PGX_GENES if pgx_data[gene]["genotype"] is None]
    
    if missing_genes:
        # Split content into lines and look for table structure
        lines = content.split('\n')
        
        # Look for header indicators
        header_found = False
        for i, line in enumerate(lines):
            if re.search(r"Gene.*Genotype.*Metabolizer", line, re.IGNORECASE):
                header_found = True
                # Start parsing from next line
                for j in range(i + 1, len(lines)):
                    parse_table_line(lines[j], pgx_data, missing_genes)
    
    return pgx_data


def parse_table_line(line: str, pgx_data: Dict, genes_to_find: List[str]):
    """
    Parse a single line from a table to extract gene data.
    
    Args:
        line: Single line of text
        pgx_data: Dictionary to update with found data
        genes_to_find: List of genes still to be found
    """
    for gene in genes_to_find:
        if gene in line:
            # Extract everything after the gene name
            remaining = line[line.index(gene) + len(gene):].strip()
            
            # Split remaining text to find genotype and status
            parts = remaining.split()
            if parts:
                # First part is likely genotype
                genotype = parts[0]
                
                # Look for metabolizer status in remaining parts
                status_parts = []
                for part in parts[1:]:
                    if any(keyword in part for keyword in ["Metabolizer", "Function", "Indeterminate"]):
                        status_parts = parts[parts.index(part):]
                        break
                    if part in ["Normal", "Intermediate", "Poor", "Rapid", "Ultra-rapid"]:
                        status_parts = [part, "Metabolizer"]
                        break
                
                metabolizer_status = " ".join(status_parts) if status_parts else "Not specified"
                
                pgx_data[gene] = {
                    "genotype": genotype,
                    "metabolizer_status": metabolizer_status
                }


def extract_pgx_data(azure_result: Dict) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Extract genotype and metabolizer status from Azure Document Intelligence results.
    
    Args:
        azure_result: Azure Document Intelligence analysis result
        
    Returns:
        Dictionary mapping gene names to their genotype and metabolizer status
    """
    try:
        # Extract text content from Azure result
        content = azure_result.get("content", "")
        return extract_pgx_data_from_content(content)
    
    except Exception as e:
        logger.error(f"Error parsing PGX data: {e}")
        # Return empty data for all genes
        return {
            gene: {"genotype": None, "metabolizer_status": None}
            for gene in PGX_GENES
        }


def format_pgx_table(pgx_data: Dict[str, Dict[str, Optional[str]]]) -> List[Dict[str, str]]:
    """
    Format PGX data as a list suitable for table display.
    
    Args:
        pgx_data: Dictionary of gene data
        
    Returns:
        List of dictionaries with gene, genotype, and metabolizer_status
    """
    return [
        {
            "gene": gene,
            "genotype": data["genotype"] or "Not found",
            "metabolizer_status": data["metabolizer_status"] or "Not found"
        }
        for gene, data in pgx_data.items()
    ]