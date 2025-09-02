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


def extract_pgx_data(azure_result: Dict) -> Dict[str, Dict[str, Optional[str]]]:
    """
    Extract genotype and metabolizer status for each PGX gene from Azure results.
    
    Args:
        azure_result: Azure Document Intelligence analysis result
        
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
    
    try:
        # Extract text content from Azure result
        content = azure_result.get("content", "")
        
        if not content:
            logger.warning("No content found in Azure result")
            return pgx_data
        
        # Find the "Patient Genotype" section
        # Look for patterns like "Gene\nGenotype\nMetabolizer Status"
        genotype_section_start = content.find("Patient Genotype")
        
        if genotype_section_start == -1:
            logger.warning("Patient Genotype section not found")
            return pgx_data
        
        # Extract the relevant section
        section = content[genotype_section_start:]
        
        # Split into lines for easier parsing
        lines = section.split('\n')
        
        # Parse the table data
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this line contains a gene name
            if line in PGX_GENES:
                gene = line
                
                # Look for genotype and metabolizer status in next lines
                genotype = None
                metabolizer_status = None
                
                # Check next few lines for genotype and metabolizer status
                for j in range(1, min(4, len(lines) - i)):
                    next_line = lines[i + j].strip()
                    
                    # Check if it's a genotype (contains *, /, or specific patterns)
                    if ('*' in next_line or '/' in next_line or 
                        'Reference' in next_line or 'c.' in next_line):
                        genotype = next_line
                    
                    # Check if it's a metabolizer status
                    elif ('Metabolizer' in next_line or 
                          'Function' in next_line or
                          'Indeterminate' in next_line):
                        metabolizer_status = next_line
                
                # Update the data
                pgx_data[gene] = {
                    "genotype": genotype,
                    "metabolizer_status": metabolizer_status
                }
                
                logger.info(f"Found {gene}: genotype={genotype}, status={metabolizer_status}")
            
            i += 1
        
        # Alternative parsing method using regex patterns
        # This handles cases where the format might be slightly different
        for gene in PGX_GENES:
            if pgx_data[gene]["genotype"] is None:
                # Try to find gene with regex
                pattern = rf"{gene}\s+([^\n]+)\s+([\w\s]+Metabolizer|[\w\s]+Function|Indeterminate)"
                match = re.search(pattern, content)
                
                if match:
                    pgx_data[gene] = {
                        "genotype": match.group(1).strip(),
                        "metabolizer_status": match.group(2).strip()
                    }
    
    except Exception as e:
        logger.error(f"Error parsing PGX data: {e}")
    
    return pgx_data


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