#!/usr/bin/env python3
"""
Test CPIC Integration

This script tests the CPIC annotation functionality with sample PGX data.
"""

from cpic_annotator import get_cpic_annotator
from schemas import PgxGeneData, CPICSummary

def test_cpic_annotation():
    """Test CPIC annotation with sample gene data."""
    
    print("=" * 70)
    print("Testing CPIC Integration")
    print("=" * 70)
    print()
    
    # Initialize annotator
    annotator = get_cpic_annotator()
    print()
    
    # Sample gene data (as would be extracted from PDF)
    sample_genes = [
        {
            'gene': 'CYP2C19',
            'genotype': '*1/*2',
            'metabolizer_status': 'Intermediate Metabolizer'
        },
        {
            'gene': 'CYP2D6',
            'genotype': '*1/*4',
            'metabolizer_status': 'Intermediate Metabolizer'
        },
        {
            'gene': 'TPMT',
            'genotype': '*1/*3A',
            'metabolizer_status': 'Intermediate Metabolizer'
        },
        {
            'gene': 'VKORC1',
            'genotype': 'Reference/rs9923231 (-1639G>A)',
            'metabolizer_status': 'Reduced Activity'
        },
        {
            'gene': 'CYP2C9',
            'genotype': '*1/*1',
            'metabolizer_status': 'Normal Metabolizer'
        },
        {
            'gene': 'DPYD',
            'genotype': '*1/*1',
            'metabolizer_status': 'Normal Metabolizer'
        },
        {
            'gene': 'SLCO1B1',
            'genotype': '*1/*1',
            'metabolizer_status': 'Normal Function'
        }
    ]
    
    print("📋 Sample Genes to Annotate:")
    print("-" * 70)
    for i, gene in enumerate(sample_genes, 1):
        print(f"{i}. {gene['gene']:15s} {gene['genotype']:30s} {gene['metabolizer_status']}")
    print()
    print()
    
    # Annotate genes
    print("🔄 Annotating with CPIC data...")
    annotated_genes = annotator.annotate_genes(sample_genes)
    print()
    
    # Display results
    print("✅ Annotated Results:")
    print("=" * 70)
    
    for gene in annotated_genes:
        print()
        print(f"🧬 {gene['gene']} - {gene['genotype']}")
        print("-" * 70)
        print(f"   Original Interpretation: {gene['metabolizer_status']}")
        print(f"   CPIC Phenotype:         {gene['cpic_phenotype'] or 'Not found'}")
        print(f"   CPIC Category:          {gene['cpic_phenotype_category'] or 'N/A'}")
        print(f"   EHR Priority:           {gene['cpic_ehr_priority'] or 'N/A'}")
        print(f"   High Risk:              {'⚠️  YES' if gene['cpic_is_high_risk'] else '✓ No'}")
        print(f"   Match Status:           {gene['cpic_match_status']}")
        if gene['cpic_validation_message']:
            print(f"   Validation:             {gene['cpic_validation_message']}")
    
    print()
    print()
    
    # Summary statistics
    print("📊 Summary Statistics:")
    print("=" * 70)
    stats = annotator.get_summary_statistics(annotated_genes)
    
    print(f"   Total genes:            {stats['total_genes']}")
    print(f"   Found in CPIC:          {stats['cpic_found']}")
    print(f"   Not found in CPIC:      {stats['cpic_not_found']}")
    print(f"   High-risk variants:     {stats['high_risk_count']}")
    print(f"   Exact matches:          {stats['exact_matches']}")
    print(f"   Mismatches:             {stats['mismatches']}")
    print(f"   Match rate:             {stats['match_rate']}%")
    
    print()
    print()
    
    # High-risk genes
    high_risk = annotator.get_high_risk_genes(annotated_genes)
    if high_risk:
        print("⚠️  High-Risk Variants Requiring Clinical Attention:")
        print("=" * 70)
        for gene in high_risk:
            print(f"   • {gene['gene']:15s} {gene['genotype']:30s}")
            print(f"     CPIC: {gene['cpic_phenotype']}")
            print(f"     Priority: {gene['cpic_ehr_priority']}")
            print()
    else:
        print("✅ No high-risk variants detected")
    
    print()
    print("=" * 70)
    print("✅ CPIC Integration Test Complete!")
    print("=" * 70)


if __name__ == "__main__":
    test_cpic_annotation()
