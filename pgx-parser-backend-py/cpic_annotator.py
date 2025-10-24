"""
CPIC Annotator - Standardize and validate PGX phenotypes using CPIC guidelines.

This module provides functionality to annotate extracted PGX gene data with
CPIC (Clinical Pharmacogenetics Implementation Consortium) standardized phenotypes.
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, List
from functools import lru_cache

logger = logging.getLogger(__name__)


class CPICAnnotator:
    """
    CPIC Phenotype Annotator
    
    Provides lookup and validation of genotype-to-phenotype mappings
    using the integrated CPIC translation table.
    """
    
    _instance = None
    _table = None
    
    def __new__(cls):
        """Singleton pattern to load CPIC table only once."""
        if cls._instance is None:
            cls._instance = super(CPICAnnotator, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize annotator with CPIC table."""
        if self._table is None:
            self._load_cpic_table()
    
    def _load_cpic_table(self):
        """Load CPIC integrated table from CSV file."""
        try:
            # Get path to CPIC table (in annotations directory)
            backend_dir = Path(__file__).parent
            project_root = backend_dir.parent
            cpic_file = project_root / "annotations" / "cpic_diplotype_phenotype_integrated.csv"
            
            if not cpic_file.exists():
                logger.error(f"CPIC table not found at: {cpic_file}")
                self._table = pd.DataFrame()
                return
            
            self._table = pd.read_csv(cpic_file)
            logger.info(f"✅ Loaded CPIC table: {len(self._table)} diplotypes for {self._table['Gene'].nunique()} genes")
            
        except Exception as e:
            logger.error(f"Error loading CPIC table: {e}")
            self._table = pd.DataFrame()
    
    @lru_cache(maxsize=1000)
    def lookup_phenotype(self, gene: str, diplotype: str) -> Optional[Dict]:
        """
        Look up CPIC phenotype for a given gene and diplotype.
        
        Args:
            gene: Gene name (e.g., 'CYP2C19')
            diplotype: Diplotype/genotype (e.g., '*1/*2')
            
        Returns:
            dict with CPIC phenotype information or None if not found
        """
        if self._table.empty:
            return None
        
        # Normalize gene name (handle variations)
        gene_normalized = self._normalize_gene_name(gene)
        
        # Try exact match first
        result = self._table[
            (self._table['Gene'] == gene_normalized) & 
            (self._table['Diplotype'] == diplotype)
        ]
        
        if result.empty:
            # Try with reversed diplotype (e.g., *2/*1 instead of *1/*2)
            diplotype_reversed = self._reverse_diplotype(diplotype)
            if diplotype_reversed != diplotype:
                result = self._table[
                    (self._table['Gene'] == gene_normalized) & 
                    (self._table['Diplotype'] == diplotype_reversed)
                ]
        
        if result.empty:
            logger.debug(f"CPIC lookup: {gene} {diplotype} not found")
            return None
        
        row = result.iloc[0]
        
        # Convert activity score to string if present, otherwise None
        activity_score = None
        if pd.notna(row['Activity_Score']):
            activity_score = str(row['Activity_Score'])
        
        return {
            'gene': row['Gene'],
            'diplotype': row['Diplotype'],
            'cpic_phenotype_full': row['Phenotype_CPIC_Format'],
            'cpic_phenotype': row['Phenotype_Simplified'],
            'phenotype_category': row['Phenotype_Category'],
            'activity_score': activity_score,
            'ehr_priority': row['EHR_Priority'],
            'is_high_risk': row['EHR_Priority'] == 'Abnormal/Priority/High Risk'
        }
    
    def annotate_gene(self, gene: str, genotype: str, metabolizer_status: str) -> Dict:
        """
        Annotate a single gene with CPIC data.
        
        Args:
            gene: Gene name
            genotype: Genotype/diplotype from PDF
            metabolizer_status: Metabolizer status from PDF
            
        Returns:
            dict with original data plus CPIC annotations
        """
        # Look up CPIC data
        cpic_data = self.lookup_phenotype(gene, genotype)
        
        # Build annotation
        annotation = {
            'gene': gene,
            'genotype': genotype,
            'metabolizer_status': metabolizer_status,
            'cpic_phenotype': None,
            'cpic_phenotype_full': None,
            'cpic_phenotype_category': None,
            'cpic_activity_score': None,
            'cpic_ehr_priority': None,
            'cpic_is_high_risk': False,
            'cpic_match_status': 'not_found',
            'cpic_validation_message': None
        }
        
        if cpic_data is None:
            annotation['cpic_validation_message'] = f'Diplotype {genotype} not found in CPIC table for {gene}'
            return annotation
        
        # Add CPIC data
        annotation['cpic_phenotype'] = cpic_data['cpic_phenotype']
        annotation['cpic_phenotype_full'] = cpic_data['cpic_phenotype_full']
        annotation['cpic_phenotype_category'] = cpic_data['phenotype_category']
        annotation['cpic_activity_score'] = cpic_data['activity_score']
        annotation['cpic_ehr_priority'] = cpic_data['ehr_priority']
        annotation['cpic_is_high_risk'] = cpic_data['is_high_risk']
        
        # Validate against reported metabolizer status
        validation = self._validate_phenotype(
            metabolizer_status, 
            cpic_data['cpic_phenotype'],
            cpic_data['phenotype_category']
        )
        
        annotation['cpic_match_status'] = validation['status']
        annotation['cpic_validation_message'] = validation.get('message')
        
        return annotation
    
    def annotate_genes(self, genes: List[Dict]) -> List[Dict]:
        """
        Annotate multiple genes with CPIC data.
        
        Args:
            genes: List of dicts with 'gene', 'genotype', 'metabolizer_status'
            
        Returns:
            List of annotated gene dicts
        """
        annotated = []
        for gene_data in genes:
            annotation = self.annotate_gene(
                gene_data.get('gene', ''),
                gene_data.get('genotype', ''),
                gene_data.get('metabolizer_status', '')
            )
            annotated.append(annotation)
        
        return annotated
    
    def _validate_phenotype(self, reported: str, cpic_phenotype: str, cpic_category: str) -> Dict:
        """
        Validate reported phenotype against CPIC standard.
        
        Args:
            reported: Metabolizer status from PDF
            cpic_phenotype: Full CPIC phenotype
            cpic_category: CPIC phenotype category
            
        Returns:
            dict with validation status and message
        """
        if not reported or not cpic_phenotype:
            return {'status': 'unknown', 'message': 'Missing data for validation'}
        
        # Normalize for comparison
        reported_norm = reported.lower().strip()
        cpic_norm = cpic_phenotype.lower().strip()
        category_norm = cpic_category.lower().strip() if cpic_category else ''
        
        # Exact match
        if reported_norm == cpic_norm:
            return {'status': 'exact_match', 'message': 'Exact match with CPIC standard'}
        
        # Category match (e.g., "Intermediate" in "CYP2C19 Intermediate Metabolizer")
        if category_norm and category_norm in reported_norm:
            return {
                'status': 'category_match', 
                'message': f'Category matches ({cpic_category}) but format differs'
            }
        
        # Check for common variations
        if self._is_phenotype_equivalent(reported_norm, cpic_norm, category_norm):
            return {
                'status': 'equivalent_match',
                'message': 'Phenotype is equivalent to CPIC standard'
            }
        
        # Mismatch
        return {
            'status': 'mismatch',
            'message': f'Reported "{reported}" does not match CPIC "{cpic_phenotype}"'
        }
    
    def _is_phenotype_equivalent(self, reported: str, cpic: str, category: str) -> bool:
        """Check if phenotypes are equivalent despite different wording."""
        # Common equivalents
        equivalents = {
            'normal': ['normal metabolizer', 'normal function', 'normal activity'],
            'intermediate': ['intermediate metabolizer', 'intermediate function', 'intermediate activity'],
            'poor': ['poor metabolizer', 'poor function', 'poor activity', 'no function'],
            'rapid': ['rapid metabolizer', 'increased function'],
            'ultrarapid': ['ultrarapid metabolizer', 'ultra-rapid metabolizer', 'ultrarapid function'],
            'reduced': ['reduced activity', 'reduced function'],
            'low': ['low activity', 'low function']
        }
        
        # Check if reported matches any equivalent of the category
        if category in equivalents:
            for equiv in equivalents[category]:
                if equiv in reported or reported in equiv:
                    return True
        
        return False
    
    def _normalize_gene_name(self, gene: str) -> str:
        """Normalize gene name to match CPIC table format."""
        # Remove common prefixes/suffixes
        gene = gene.strip().upper()
        
        # Handle special cases
        if 'CYP2C' in gene and 'CLUSTER' in gene:
            return 'CYP2C_CLUSTER'
        
        return gene
    
    def _reverse_diplotype(self, diplotype: str) -> str:
        """Reverse diplotype (e.g., *1/*2 -> *2/*1)."""
        if '/' not in diplotype:
            return diplotype
        
        parts = diplotype.split('/')
        if len(parts) == 2:
            return f"{parts[1]}/{parts[0]}"
        
        return diplotype
    
    def get_high_risk_genes(self, annotated_genes: List[Dict]) -> List[Dict]:
        """
        Filter annotated genes to return only high-risk variants.
        
        Args:
            annotated_genes: List of annotated gene dicts
            
        Returns:
            List of high-risk genes
        """
        return [g for g in annotated_genes if g.get('cpic_is_high_risk', False)]
    
    def get_summary_statistics(self, annotated_genes: List[Dict]) -> Dict:
        """
        Get summary statistics for annotated genes.
        
        Args:
            annotated_genes: List of annotated gene dicts
            
        Returns:
            dict with summary statistics
        """
        total = len(annotated_genes)
        high_risk = len([g for g in annotated_genes if g.get('cpic_is_high_risk', False)])
        found = len([g for g in annotated_genes if g.get('cpic_match_status') != 'not_found'])
        exact_match = len([g for g in annotated_genes if g.get('cpic_match_status') == 'exact_match'])
        mismatch = len([g for g in annotated_genes if g.get('cpic_match_status') == 'mismatch'])
        
        return {
            'total_genes': total,
            'cpic_found': found,
            'cpic_not_found': total - found,
            'high_risk_count': high_risk,
            'exact_matches': exact_match,
            'mismatches': mismatch,
            'match_rate': round(exact_match / total * 100, 1) if total > 0 else 0
        }


# Global instance
_annotator = None

def get_cpic_annotator() -> CPICAnnotator:
    """Get or create global CPIC annotator instance."""
    global _annotator
    if _annotator is None:
        _annotator = CPICAnnotator()
    return _annotator
