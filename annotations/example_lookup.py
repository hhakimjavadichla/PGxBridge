#!/usr/bin/env python3
"""
Example: Using CPIC Integrated Table for Phenotype Lookup

This script demonstrates how to use the integrated CPIC translation table
to standardize and validate genotype-to-phenotype mappings.

Author: PGX Parser Project
Date: October 2025
"""

import pandas as pd
from pathlib import Path

class CPICAnnotator:
    """
    CPIC Phenotype Annotator
    
    Provides lookup and validation of genotype-to-phenotype mappings
    using the integrated CPIC translation table.
    """
    
    def __init__(self, cpic_table_path):
        """
        Initialize annotator with CPIC table.
        
        Args:
            cpic_table_path: Path to integrated CPIC CSV file
        """
        self.table = pd.read_csv(cpic_table_path)
        print(f"✅ Loaded CPIC table: {len(self.table)} diplotypes for {self.table['Gene'].nunique()} genes")
    
    def lookup_phenotype(self, gene, diplotype):
        """
        Look up phenotype for a given gene and diplotype.
        
        Args:
            gene: Gene name (e.g., 'CYP2C19')
            diplotype: Diplotype (e.g., '*1/*2')
            
        Returns:
            dict with phenotype information or None if not found
        """
        result = self.table[
            (self.table['Gene'] == gene) & 
            (self.table['Diplotype'] == diplotype)
        ]
        
        if result.empty:
            return None
        
        row = result.iloc[0]
        return {
            'gene': row['Gene'],
            'diplotype': row['Diplotype'],
            'phenotype': row['Phenotype'],
            'phenotype_category': row['Phenotype_Category'],
            'activity_score': row['Activity_Score'],
            'ehr_priority': row['EHR_Priority']
        }
    
    def validate_phenotype(self, gene, diplotype, reported_phenotype):
        """
        Validate a reported phenotype against CPIC standard.
        
        Args:
            gene: Gene name
            diplotype: Diplotype
            reported_phenotype: Phenotype reported in PDF
            
        Returns:
            dict with validation results
        """
        cpic_data = self.lookup_phenotype(gene, diplotype)
        
        if cpic_data is None:
            return {
                'valid': False,
                'status': 'not_found',
                'message': f'Diplotype {diplotype} not found in CPIC table for {gene}'
            }
        
        # Normalize phenotypes for comparison
        reported_norm = reported_phenotype.lower().strip()
        cpic_norm = cpic_data['phenotype'].lower().strip()
        
        # Check if they match
        if reported_norm == cpic_norm:
            return {
                'valid': True,
                'status': 'exact_match',
                'cpic_phenotype': cpic_data['phenotype'],
                'phenotype_category': cpic_data['phenotype_category'],
                'ehr_priority': cpic_data['ehr_priority']
            }
        
        # Check if category matches (more lenient)
        if cpic_data['phenotype_category'].lower() in reported_norm:
            return {
                'valid': True,
                'status': 'category_match',
                'cpic_phenotype': cpic_data['phenotype'],
                'reported_phenotype': reported_phenotype,
                'phenotype_category': cpic_data['phenotype_category'],
                'ehr_priority': cpic_data['ehr_priority'],
                'message': 'Phenotype category matches but format differs'
            }
        
        # Mismatch
        return {
            'valid': False,
            'status': 'mismatch',
            'cpic_phenotype': cpic_data['phenotype'],
            'reported_phenotype': reported_phenotype,
            'message': f'Reported phenotype does not match CPIC standard'
        }
    
    def get_high_risk_diplotypes(self, gene=None):
        """
        Get all high-risk diplotypes (requiring clinical attention).
        
        Args:
            gene: Optional gene name to filter by
            
        Returns:
            DataFrame of high-risk diplotypes
        """
        high_risk = self.table[
            self.table['EHR_Priority'] == 'Abnormal/Priority/High Risk'
        ]
        
        if gene:
            high_risk = high_risk[high_risk['Gene'] == gene]
        
        return high_risk
    
    def get_gene_summary(self, gene):
        """
        Get summary statistics for a gene.
        
        Args:
            gene: Gene name
            
        Returns:
            dict with gene statistics
        """
        gene_data = self.table[self.table['Gene'] == gene]
        
        if gene_data.empty:
            return None
        
        return {
            'gene': gene,
            'total_diplotypes': len(gene_data),
            'phenotype_categories': gene_data['Phenotype_Category'].value_counts().to_dict(),
            'high_risk_count': len(gene_data[gene_data['EHR_Priority'] == 'Abnormal/Priority/High Risk']),
            'normal_count': len(gene_data[gene_data['EHR_Priority'] == 'Normal/Routine/Low Risk']),
            'indeterminate_count': len(gene_data[gene_data['EHR_Priority'] == 'none'])
        }


def main():
    """Demonstration of CPIC annotator usage."""
    
    print("=" * 70)
    print("CPIC Phenotype Annotator - Example Usage")
    print("=" * 70)
    print()
    
    # Initialize annotator
    script_dir = Path(__file__).parent
    cpic_file = script_dir / "cpic_diplotype_phenotype_integrated.csv"
    
    annotator = CPICAnnotator(cpic_file)
    print()
    
    # Example 1: Simple lookup
    print("📋 Example 1: Simple Phenotype Lookup")
    print("-" * 70)
    
    examples = [
        ('CYP2C19', '*1/*2'),
        ('CYP2D6', '*1/*4'),
        ('VKORC1', 'Reference/rs9923231 (-1639G>A)'),
        ('TPMT', '*1/*3A')
    ]
    
    for gene, diplotype in examples:
        result = annotator.lookup_phenotype(gene, diplotype)
        if result:
            print(f"\n🧬 {gene} {diplotype}")
            print(f"   Phenotype: {result['phenotype']}")
            print(f"   Category: {result['phenotype_category']}")
            print(f"   Priority: {result['ehr_priority']}")
        else:
            print(f"\n❌ {gene} {diplotype} - Not found")
    
    print()
    print()
    
    # Example 2: Validation
    print("📋 Example 2: Phenotype Validation")
    print("-" * 70)
    
    validation_cases = [
        ('CYP2C19', '*1/*2', 'CYP2C19 Intermediate Metabolizer'),  # Exact match
        ('CYP2C19', '*1/*2', 'Intermediate Metabolizer'),  # Category match
        ('CYP2C19', '*1/*2', 'Normal Metabolizer'),  # Mismatch
    ]
    
    for gene, diplotype, reported in validation_cases:
        result = annotator.validate_phenotype(gene, diplotype, reported)
        print(f"\n🔍 {gene} {diplotype}")
        print(f"   Reported: {reported}")
        print(f"   Status: {result['status']}")
        if 'cpic_phenotype' in result:
            print(f"   CPIC Standard: {result['cpic_phenotype']}")
        if 'message' in result:
            print(f"   Note: {result['message']}")
    
    print()
    print()
    
    # Example 3: High-risk diplotypes
    print("📋 Example 3: High-Risk Diplotypes")
    print("-" * 70)
    
    for gene in ['CYP2C19', 'TPMT', 'DPYD']:
        high_risk = annotator.get_high_risk_diplotypes(gene)
        print(f"\n⚠️  {gene}: {len(high_risk)} high-risk diplotypes")
        if len(high_risk) > 0:
            print(f"   Examples: {', '.join(high_risk['Diplotype'].head(5).tolist())}")
    
    print()
    print()
    
    # Example 4: Gene summary
    print("📋 Example 4: Gene Summary Statistics")
    print("-" * 70)
    
    for gene in ['CYP2C19', 'CYP2D6', 'TPMT']:
        summary = annotator.get_gene_summary(gene)
        if summary:
            print(f"\n📊 {gene}")
            print(f"   Total diplotypes: {summary['total_diplotypes']}")
            print(f"   High-risk: {summary['high_risk_count']}")
            print(f"   Normal: {summary['normal_count']}")
            print(f"   Indeterminate: {summary['indeterminate_count']}")
            print(f"   Categories: {', '.join([f'{k}={v}' for k, v in list(summary['phenotype_categories'].items())[:3]])}")
    
    print()
    print()
    print("✅ Examples complete!")
    print()


if __name__ == "__main__":
    main()
