# CPIC Translation Tables - Integrated Reference

This directory contains CPIC (Clinical Pharmacogenetics Implementation Consortium) diplotype-to-phenotype translation tables for standardizing pharmacogenomics annotations.

## 📁 Files

### Source Files
- **`CPIC translations/`** - Individual CPIC translation tables (15 genes)
  - Original CSV files downloaded from CPIC
  - One file per gene with diplotype-to-phenotype mappings

### Integrated File
- **`cpic_diplotype_phenotype_integrated.csv`** - Consolidated translation table
  - **Size:** 1.8 MB
  - **Rows:** 27,170 (27,169 diplotypes + 1 header)
  - **Genes:** 15 pharmacogenes
  - **Created:** October 23, 2025

### Script
- **`integrate_cpic_tables.py`** - Python script to regenerate integrated file

## 📊 Integrated File Structure

### Columns

| Column | Description | Example |
|--------|-------------|---------|
| **Gene** | Gene name | `CYP2C19` |
| **Diplotype** | Diplotype/genotype | `*1/*2` |
| **Phenotype** | Full phenotype description | `CYP2C19 Intermediate Metabolizer` |
| **Phenotype_Category** | Standardized category | `Intermediate` |
| **Activity_Score** | Activity score (if available) | `n/a` or numeric |
| **EHR_Priority** | Clinical priority notation | `Abnormal/Priority/High Risk` |

### Phenotype Categories

The `Phenotype_Category` column standardizes phenotypes into these categories:

- **Normal** - Normal metabolizer/activity
- **Intermediate** - Intermediate metabolizer/activity
- **Poor** - Poor metabolizer/activity
- **Rapid** - Rapid metabolizer
- **Ultrarapid** - Ultrarapid metabolizer
- **Reduced** - Reduced activity
- **Low** - Low activity
- **Indeterminate** - Cannot determine phenotype
- **Unknown** - Unknown phenotype

### EHR Priority Levels

- **Normal/Routine/Low Risk** - Standard dosing applies
- **Abnormal/Priority/High Risk** - Requires dose adjustment or alternative therapy
- **none** - No specific priority (indeterminate cases)

## 🧬 Genes Included

| Gene | Full Name | Diplotypes | Clinical Use |
|------|-----------|------------|--------------|
| **CYP2B6** | Cytochrome P450 2B6 | 1,176 | Efavirenz, nevirapine |
| **CYP2C19** | Cytochrome P450 2C19 | 666 | Clopidogrel, SSRIs, PPIs |
| **CYP2C9** | Cytochrome P450 2C9 | 2,850 | Warfarin, NSAIDs, phenytoin |
| **CYP2C_CLUSTER** | CYP2C Cluster | 3 | Combined CYP2C genes |
| **CYP2D6** | Cytochrome P450 2D6 | 16,836 | Codeine, tamoxifen, SSRIs |
| **CYP3A5** | Cytochrome P450 3A5 | 21 | Tacrolimus, immunosuppressants |
| **CYP4F2** | Cytochrome P450 4F2 | 5 | Warfarin (vitamin K metabolism) |
| **DPYD** | Dihydropyrimidine Dehydrogenase | 3,570 | Fluoropyrimidines (5-FU, capecitabine) |
| **HLA** | Human Leukocyte Antigen | 9 | Abacavir, carbamazepine hypersensitivity |
| **IFNL4** | Interferon Lambda 4 | 3 | Hepatitis C treatment |
| **NUDT15** | Nudix Hydrolase 15 | 46 | Thiopurines (azathioprine, mercaptopurine) |
| **SLCO1B1** | Solute Carrier Organic Anion Transporter | 990 | Simvastatin toxicity |
| **TPMT** | Thiopurine S-Methyltransferase | 946 | Thiopurines (azathioprine, mercaptopurine) |
| **UGT1A1** | UDP Glucuronosyltransferase 1A1 | 45 | Irinotecan toxicity |
| **VKORC1** | Vitamin K Epoxide Reductase Complex 1 | 3 | Warfarin dosing |

**Total:** 27,169 diplotype-to-phenotype mappings

## 🔄 Usage in PGX Parser Pipeline

### Purpose
This integrated table will be used to:
1. **Standardize phenotypes** extracted from PDF reports
2. **Validate** genotype-phenotype assignments
3. **Annotate** results with CPIC-compliant phenotypes
4. **Flag high-risk** variants requiring clinical attention

### Integration Steps (Future)

1. **Extract genotype** from PDF (e.g., `CYP2C19 *1/*2`)
2. **Look up** in integrated table
3. **Return standardized phenotype:**
   - Phenotype: `CYP2C19 Intermediate Metabolizer`
   - Category: `Intermediate`
   - Priority: `Abnormal/Priority/High Risk`
4. **Add to output** for clinical decision support

### Example Lookup

```python
import pandas as pd

# Load integrated table
cpic_table = pd.read_csv('cpic_diplotype_phenotype_integrated.csv')

# Look up a diplotype
gene = 'CYP2C19'
diplotype = '*1/*2'

result = cpic_table[
    (cpic_table['Gene'] == gene) & 
    (cpic_table['Diplotype'] == diplotype)
]

print(result)
# Output:
# Gene: CYP2C19
# Diplotype: *1/*2
# Phenotype: CYP2C19 Intermediate Metabolizer
# Phenotype_Category: Intermediate
# EHR_Priority: Abnormal/Priority/High Risk
```

## 🔧 Regenerating the Integrated File

If you need to update the integrated file (e.g., after adding new CPIC tables):

```bash
cd annotations
python integrate_cpic_tables.py
```

This will:
1. Read all CSV files from `CPIC translations/` directory
2. Extract gene names from filenames
3. Standardize column names
4. Add phenotype categories
5. Combine into single CSV
6. Sort by gene and diplotype
7. Save as `cpic_diplotype_phenotype_integrated.csv`

## 📚 Data Source

All translation tables are sourced from:
- **CPIC (Clinical Pharmacogenetics Implementation Consortium)**
- Website: https://cpicpgx.org/
- Guidelines: https://cpicpgx.org/guidelines/

### Citation
If using this data in publications, please cite CPIC:
> Clinical Pharmacogenetics Implementation Consortium (CPIC®). 
> Available at: https://cpicpgx.org/

## 📊 Statistics

- **Total genes:** 15
- **Total diplotypes:** 27,169
- **File size:** 1.8 MB
- **Format:** CSV (comma-separated values)
- **Encoding:** UTF-8

### Distribution by Gene

```
CYP2D6    : 16,836 diplotypes (62.0%)
DPYD      :  3,570 diplotypes (13.1%)
CYP2C9    :  2,850 diplotypes (10.5%)
CYP2B6    :  1,176 diplotypes ( 4.3%)
SLCO1B1   :    990 diplotypes ( 3.6%)
TPMT      :    946 diplotypes ( 3.5%)
CYP2C19   :    666 diplotypes ( 2.5%)
NUDT15    :     46 diplotypes ( 0.2%)
UGT1A1    :     45 diplotypes ( 0.2%)
CYP3A5    :     21 diplotypes ( 0.1%)
HLA       :      9 diplotypes ( 0.0%)
CYP4F2    :      5 diplotypes ( 0.0%)
VKORC1    :      3 diplotypes ( 0.0%)
CYP2C_CLUSTER:   3 diplotypes ( 0.0%)
IFNL4     :      3 diplotypes ( 0.0%)
```

## 🔍 Quality Notes

### Phenotype Category Extraction
The `Phenotype_Category` column is automatically extracted from the full phenotype description using pattern matching. This standardizes variations like:
- "CYP2C19 Intermediate Metabolizer" → `Intermediate`
- "VKORC1 Reduced Activity" → `Reduced`
- "TPMT Indeterminate" → `Indeterminate`

### Activity Scores
Most entries have `n/a` for Activity Score. Some genes (like CYP2D6) may have numeric activity scores in future CPIC updates.

### Indeterminate Cases
Diplotypes marked as "Indeterminate" typically represent:
- Novel or rare alleles with unknown function
- Combinations requiring additional testing
- Cases where phenotype cannot be reliably predicted

## 🎯 Next Steps

### Planned Integration
1. **Create lookup function** in backend (`cpic_annotator.py`)
2. **Add validation** to compare PDF phenotypes with CPIC standard
3. **Implement flagging** for high-risk variants
4. **Add to API response** with CPIC annotations
5. **Update frontend** to display CPIC-standardized phenotypes

### Future Enhancements
- Add drug-gene interaction mappings
- Include dosing recommendations
- Link to CPIC guideline URLs
- Add allele frequency data
- Include population-specific information

## 📞 Maintenance

**Last Updated:** October 23, 2025  
**Script Version:** 1.0  
**CPIC Data Version:** Check individual files in `CPIC translations/` directory

To update with new CPIC data:
1. Download updated tables from CPIC website
2. Place in `CPIC translations/` directory
3. Run `python integrate_cpic_tables.py`
4. Verify output with sample lookups
5. Update this README with new statistics

---

**Note:** This integrated table is for research and clinical decision support. Always refer to official CPIC guidelines and consult with clinical pharmacists for patient-specific recommendations.
