#!/usr/bin/env python3
"""
Integrate CPIC Translation Tables

This script combines all individual CPIC gene diplotype-to-phenotype translation
tables into a single consolidated CSV file for standardized phenotype annotation.

Author: PGX Parser Project
Date: October 2025
"""

import pandas as pd
import os
from pathlib import Path
import re

def extract_gene_name(filename):
    """
    Extract gene name from filename.
    
    Examples:
        'CYP2C19_Diplotype_Phenotype_Table (23).csv' -> 'CYP2C19'
        'VKORC1_Diplotype_Phenotype_Table.csv' -> 'VKORC1'
        'CYP2C cluster_Diplotype_Phenotype_Table.csv' -> 'CYP2C_CLUSTER'
    """
    # Remove file extension
    name = filename.replace('.csv', '')
    
    # Extract gene name (everything before '_Diplotype')
    match = re.match(r'^([A-Z0-9]+(?:\s+[A-Za-z]+)?)', name)
    if match:
        gene = match.group(1).strip()
        # Replace spaces with underscores and convert to uppercase
        gene = gene.replace(' ', '_').upper()
        return gene
    
    return 'UNKNOWN'

def integrate_cpic_tables(input_dir, output_file):
    """
    Integrate all CPIC translation tables into a single CSV file.
    
    Args:
        input_dir: Directory containing individual CPIC CSV files
        output_file: Path to output integrated CSV file
    """
    input_path = Path(input_dir)
    
    # Find all CSV files
    csv_files = sorted(input_path.glob('*.csv'))
    
    if not csv_files:
        print(f"❌ No CSV files found in {input_dir}")
        return
    
    print(f"📁 Found {len(csv_files)} CPIC translation tables")
    print()
    
    all_data = []
    gene_counts = {}
    
    for csv_file in csv_files:
        # Skip .DS_Store and other hidden files
        if csv_file.name.startswith('.'):
            continue
        
        # Extract gene name from filename
        gene_name = extract_gene_name(csv_file.name)
        
        try:
            # Read CSV file
            df = pd.read_csv(csv_file)
            
            # Get the diplotype column name (first column)
            diplotype_col = df.columns[0]
            
            # Add gene column
            df.insert(0, 'Gene', gene_name)
            
            # Rename columns to standardized names
            column_mapping = {
                diplotype_col: 'Diplotype',
                'Activity Score': 'Activity_Score',
                'Coded Diplotype/Phenotype Summary': 'Phenotype',
                'EHR Priority Notation': 'EHR_Priority'
            }
            
            df = df.rename(columns=column_mapping)
            
            # Process phenotype columns
            if 'Phenotype' in df.columns:
                # Store original CPIC format
                df['Phenotype_CPIC_Format'] = df['Phenotype']
                
                # Extract simplified phenotype (remove gene name prefix)
                # e.g., "CYP2B6 Normal Metabolizer" -> "Normal Metabolizer"
                df['Phenotype_Simplified'] = df['Phenotype'].str.replace(
                    rf'^{gene_name}\s+', '', regex=True
                )
                
                # Extract phenotype category (e.g., "Normal" from "Normal Metabolizer")
                df['Phenotype_Category'] = df['Phenotype'].str.extract(
                    r'(Normal|Intermediate|Poor|Rapid|Ultrarapid|Ultra[- ]?rapid|Likely Intermediate|Possible Intermediate|Reduced|Low|Indeterminate|Unknown)(?:\s+(?:Metabolizer|Activity|Function))?', 
                    expand=False
                )
                df['Phenotype_Category'] = df['Phenotype_Category'].fillna('Unknown')
            
            # Add to collection
            all_data.append(df)
            gene_counts[gene_name] = len(df)
            
            print(f"✅ {gene_name:20s} - {len(df):4d} diplotypes")
            
        except Exception as e:
            print(f"❌ Error processing {csv_file.name}: {e}")
            continue
    
    if not all_data:
        print("❌ No data to integrate")
        return
    
    # Combine all dataframes
    print()
    print("🔄 Combining all tables...")
    integrated_df = pd.concat(all_data, ignore_index=True)
    
    # Reorder columns for better readability
    column_order = ['Gene', 'Diplotype', 'Phenotype_CPIC_Format', 'Phenotype_Simplified', 
                   'Phenotype_Category', 'Activity_Score', 'EHR_Priority']
    
    # Only include columns that exist
    column_order = [col for col in column_order if col in integrated_df.columns]
    integrated_df = integrated_df[column_order]
    
    # Sort by gene and diplotype
    integrated_df = integrated_df.sort_values(['Gene', 'Diplotype'], ignore_index=True)
    
    # Save to CSV
    integrated_df.to_csv(output_file, index=False)
    
    print(f"✅ Integrated table saved to: {output_file}")
    print()
    print("📊 Summary:")
    print(f"   Total genes: {len(gene_counts)}")
    print(f"   Total diplotypes: {len(integrated_df)}")
    print()
    print("📋 Genes included:")
    for gene, count in sorted(gene_counts.items()):
        print(f"   {gene:20s} {count:4d} diplotypes")
    print()
    print("🎯 Column structure:")
    for i, col in enumerate(integrated_df.columns, 1):
        print(f"   {i}. {col}")
    print()
    print("✅ Integration complete!")

def main():
    """Main execution function."""
    # Set paths
    script_dir = Path(__file__).parent
    input_dir = script_dir / "CPIC translations"
    output_file = script_dir / "cpic_diplotype_phenotype_integrated.csv"
    
    print("=" * 70)
    print("CPIC Translation Tables Integration")
    print("=" * 70)
    print()
    
    # Check if input directory exists
    if not input_dir.exists():
        print(f"❌ Input directory not found: {input_dir}")
        return
    
    # Run integration
    integrate_cpic_tables(input_dir, output_file)
    
    # Show preview
    print("📄 Preview of integrated table (first 10 rows):")
    print()
    df = pd.read_csv(output_file)
    print(df.head(10).to_string(index=False))
    print()
    print(f"... and {len(df) - 10} more rows")

if __name__ == "__main__":
    main()
