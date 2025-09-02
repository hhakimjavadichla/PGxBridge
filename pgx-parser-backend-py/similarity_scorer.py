"""
Similarity scoring utilities for comparing LLM vs Document Intelligence extraction results.
"""

import re
from typing import Optional, Dict, Any
from difflib import SequenceMatcher
from datetime import datetime


def normalize_text(text: Optional[str]) -> str:
    """Normalize text for comparison by removing extra spaces, punctuation, and converting to lowercase."""
    if not text or text in ["Not found", "None", ""]:
        return ""
    
    # Convert to string and lowercase
    text = str(text).lower().strip()
    
    # Remove extra whitespace and punctuation
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^\w\s]', '', text)
    
    return text


def normalize_date(date_str: Optional[str]) -> str:
    """Normalize date strings for comparison."""
    if not date_str or date_str in ["Not found", "None", ""]:
        return ""
    
    # Remove common date formatting variations
    date_str = str(date_str).strip()
    date_str = re.sub(r'[,\-/]', ' ', date_str)
    date_str = re.sub(r'\s+', ' ', date_str)
    
    return date_str.lower()


def calculate_text_similarity(text1: Optional[str], text2: Optional[str]) -> float:
    """
    Calculate similarity score between two text strings.
    Returns a score between 0.0 (completely different) and 1.0 (identical).
    """
    norm1 = normalize_text(text1)
    norm2 = normalize_text(text2)
    
    # Handle empty/missing values
    if not norm1 and not norm2:
        return 1.0  # Both empty/missing
    if not norm1 or not norm2:
        return 0.0  # One empty, one has value
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Use sequence matcher for similarity
    similarity = SequenceMatcher(None, norm1, norm2).ratio()
    
    # Boost score for partial matches in names, IDs, etc.
    if len(norm1) > 3 and len(norm2) > 3:
        # Check if one is contained in the other
        if norm1 in norm2 or norm2 in norm1:
            similarity = max(similarity, 0.8)
    
    return round(similarity, 3)


def calculate_date_similarity(date1: Optional[str], date2: Optional[str]) -> float:
    """Calculate similarity for date fields with special handling for date formats."""
    norm1 = normalize_date(date1)
    norm2 = normalize_date(date2)
    
    # Handle empty/missing values
    if not norm1 and not norm2:
        return 1.0
    if not norm1 or not norm2:
        return 0.0
    
    # Exact match after normalization
    if norm1 == norm2:
        return 1.0
    
    # Try to extract date components for comparison
    def extract_date_parts(date_str):
        # Extract numbers that could be day, month, year
        numbers = re.findall(r'\d+', date_str)
        return set(numbers)
    
    parts1 = extract_date_parts(norm1)
    parts2 = extract_date_parts(norm2)
    
    if parts1 and parts2:
        # Calculate overlap of date components
        intersection = len(parts1.intersection(parts2))
        union = len(parts1.union(parts2))
        if union > 0:
            component_similarity = intersection / union
            # Use higher of component similarity or text similarity
            text_similarity = SequenceMatcher(None, norm1, norm2).ratio()
            return round(max(component_similarity, text_similarity), 3)
    
    # Fall back to text similarity
    return round(SequenceMatcher(None, norm1, norm2).ratio(), 3)


def calculate_genotype_similarity(genotype1: Optional[str], genotype2: Optional[str]) -> float:
    """Calculate similarity for genotype fields with special handling for genetic notation."""
    if not genotype1 or not genotype2:
        return 0.0 if (genotype1 or genotype2) else 1.0
    
    # Normalize genetic notation
    def normalize_genotype(genotype):
        if not genotype or genotype in ["Not found", "None", ""]:
            return ""
        
        genotype = str(genotype).strip()
        # Remove common variations in genetic notation
        genotype = re.sub(r'[(),\s]', '', genotype)
        return genotype.lower()
    
    norm1 = normalize_genotype(genotype1)
    norm2 = normalize_genotype(genotype2)
    
    if not norm1 and not norm2:
        return 1.0
    if not norm1 or not norm2:
        return 0.0
    
    if norm1 == norm2:
        return 1.0
    
    # Special handling for allele notation (e.g., *1/*2 vs *2/*1)
    if '*' in norm1 and '*' in norm2:
        # Extract alleles
        alleles1 = set(re.findall(r'\*\w+', norm1))
        alleles2 = set(re.findall(r'\*\w+', norm2))
        
        if alleles1 and alleles2:
            if alleles1 == alleles2:
                return 1.0
            # Partial overlap
            intersection = len(alleles1.intersection(alleles2))
            union = len(alleles1.union(alleles2))
            if union > 0:
                return round(intersection / union, 3)
    
    # Fall back to text similarity
    return round(SequenceMatcher(None, norm1, norm2).ratio(), 3)


def calculate_field_similarity(field_name: str, value1: Optional[str], value2: Optional[str]) -> float:
    """
    Calculate similarity based on field type.
    """
    # Date fields
    if any(date_keyword in field_name.lower() for date_keyword in ['date', 'birth']):
        return calculate_date_similarity(value1, value2)
    
    # Genotype fields
    if 'genotype' in field_name.lower():
        return calculate_genotype_similarity(value1, value2)
    
    # Default to text similarity
    return calculate_text_similarity(value1, value2)


def compare_patient_info(llm_patient: Dict[str, Any], di_patient: Dict[str, Any]) -> Dict[str, float]:
    """Compare patient information and return similarity scores for each field."""
    similarity_scores = {}
    
    # Get all unique field names from both sources
    all_fields = set(llm_patient.keys()).union(set(di_patient.keys()))
    
    for field in all_fields:
        llm_value = llm_patient.get(field)
        di_value = di_patient.get(field)
        
        similarity_scores[field] = calculate_field_similarity(field, llm_value, di_value)
    
    return similarity_scores


def compare_pgx_genes(llm_genes: list, di_genes: list) -> Dict[str, Dict[str, float]]:
    """Compare PGX gene data and return similarity scores for each gene and field."""
    gene_similarities = {}
    
    # Create lookup dictionaries
    llm_gene_dict = {gene.gene: gene for gene in llm_genes}
    di_gene_dict = {gene.gene: gene for gene in di_genes}
    
    # Get all unique gene names
    all_genes = set(llm_gene_dict.keys()).union(set(di_gene_dict.keys()))
    
    for gene_name in all_genes:
        llm_gene = llm_gene_dict.get(gene_name)
        di_gene = di_gene_dict.get(gene_name)
        
        gene_similarities[gene_name] = {}
        
        # Compare genotype
        llm_genotype = llm_gene.genotype if llm_gene else None
        di_genotype = di_gene.genotype if di_gene else None
        gene_similarities[gene_name]['genotype'] = calculate_genotype_similarity(llm_genotype, di_genotype)
        
        # Compare metabolizer status
        llm_status = llm_gene.metabolizer_status if llm_gene else None
        di_status = di_gene.metabolizer_status if di_gene else None
        gene_similarities[gene_name]['metabolizer_status'] = calculate_text_similarity(llm_status, di_status)
    
    return gene_similarities
