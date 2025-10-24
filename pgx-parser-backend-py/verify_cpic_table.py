#!/usr/bin/env python3
"""
Verify CPIC Table is loaded correctly
"""

from cpic_annotator import get_cpic_annotator

def verify_cpic_table():
    """Verify CPIC table structure and sample lookups."""
    
    print("=" * 70)
    print("CPIC Table Verification")
    print("=" * 70)
    print()
    
    # Get annotator
    annotator = get_cpic_annotator()
    
    # Check table structure
    print("📋 Table Structure:")
    print(f"   Columns: {list(annotator._table.columns)}")
    print(f"   Total rows: {len(annotator._table)}")
    print(f"   Genes: {annotator._table['Gene'].nunique()}")
    print()
    
    # Test lookups from your PDF
    test_cases = [
        ('CYP2B6', '*6/*6', 'Poor Metabolizer'),
        ('CYP2C19', '*17/*17', 'Ultrarapid Metabolizer'),
        ('CYP2C9', '*1/*1', 'Normal Metabolizer'),
        ('CYP2D6', '*20/*41', 'Intermediate Metabolizer'),
        ('NUDT15', '*1/*1', 'Normal Metabolizer'),
        ('TPMT', '*1/*1', 'Normal Metabolizer'),
    ]
    
    print("🔍 Testing Lookups:")
    print("-" * 70)
    
    found_count = 0
    for gene, diplotype, expected in test_cases:
        result = annotator.lookup_phenotype(gene, diplotype)
        if result:
            found_count += 1
            status = "✅ FOUND"
            phenotype = result['cpic_phenotype']
            match = "✓" if phenotype == expected else "✗"
        else:
            status = "❌ NOT FOUND"
            phenotype = "N/A"
            match = "✗"
        
        print(f"{status} {gene:10s} {diplotype:15s}")
        print(f"         Expected: {expected}")
        print(f"         CPIC:     {phenotype} {match}")
        print()
    
    print("=" * 70)
    print(f"Summary: {found_count}/{len(test_cases)} genotypes found in CPIC table")
    print("=" * 70)
    
    if found_count == len(test_cases):
        print("✅ All test genotypes found! CPIC table is working correctly.")
    else:
        print("⚠️  Some genotypes not found. Check if CPIC table is loaded correctly.")
    
    print()

if __name__ == "__main__":
    verify_cpic_table()
