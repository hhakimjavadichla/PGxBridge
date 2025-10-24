# CPIC Tables Integration - Summary

**Date:** October 23, 2025  
**Status:** ✅ Complete

## 🎯 Objective

Integrate multiple CPIC (Clinical Pharmacogenetics Implementation Consortium) translation tables into a single CSV file for standardizing patient phenotypes parsed from PDF files.

## ✅ What Was Done

### 1. Created Integration Script
**File:** `integrate_cpic_tables.py`

- Reads all 15 individual CPIC CSV files from `CPIC translations/` directory
- Extracts gene names from filenames
- Standardizes column names across all tables
- Adds `Phenotype_Category` column for easy filtering
- Combines into single consolidated CSV
- Sorts by gene and diplotype

### 2. Generated Integrated File
**File:** `cpic_diplotype_phenotype_integrated.csv`

**Statistics:**
- **Size:** 1.8 MB
- **Total rows:** 27,170 (including header)
- **Total diplotypes:** 27,169
- **Genes covered:** 15 pharmacogenes
- **Format:** CSV with 6 columns

**Columns:**
1. `Gene` - Gene name (e.g., CYP2C19)
2. `Diplotype` - Genotype/diplotype (e.g., *1/*2)
3. `Phenotype` - Full CPIC phenotype description
4. `Phenotype_Category` - Standardized category (Normal, Intermediate, Poor, etc.)
5. `Activity_Score` - Activity score (if available)
6. `EHR_Priority` - Clinical priority level

### 3. Created Documentation
**File:** `README.md`

- Complete documentation of integrated file structure
- Gene descriptions and clinical uses
- Usage examples
- Statistics and distribution
- Maintenance instructions

### 4. Created Example Code
**File:** `example_lookup.py`

- `CPICAnnotator` class for phenotype lookups
- Validation functions
- High-risk diplotype identification
- Gene summary statistics
- Working examples demonstrating all features

## 📊 Genes Included

| Gene | Diplotypes | % of Total | Clinical Use |
|------|------------|------------|--------------|
| CYP2D6 | 16,836 | 62.0% | Codeine, tamoxifen, SSRIs |
| DPYD | 3,570 | 13.1% | Fluoropyrimidines (5-FU) |
| CYP2C9 | 2,850 | 10.5% | Warfarin, NSAIDs |
| CYP2B6 | 1,176 | 4.3% | Efavirenz, nevirapine |
| SLCO1B1 | 990 | 3.6% | Simvastatin toxicity |
| TPMT | 946 | 3.5% | Thiopurines |
| CYP2C19 | 666 | 2.5% | Clopidogrel, SSRIs |
| NUDT15 | 46 | 0.2% | Thiopurines |
| UGT1A1 | 45 | 0.2% | Irinotecan |
| CYP3A5 | 21 | 0.1% | Tacrolimus |
| HLA | 9 | 0.0% | Abacavir hypersensitivity |
| CYP4F2 | 5 | 0.0% | Warfarin (vitamin K) |
| VKORC1 | 3 | 0.0% | Warfarin dosing |
| CYP2C_CLUSTER | 3 | 0.0% | Combined CYP2C |
| IFNL4 | 3 | 0.0% | Hepatitis C treatment |

**Total:** 27,169 diplotype-to-phenotype mappings

## 🔍 Key Features

### Phenotype Categories
Standardized into these categories:
- **Normal** - Normal metabolizer/activity
- **Intermediate** - Intermediate metabolizer/activity
- **Poor** - Poor metabolizer/activity
- **Rapid** - Rapid metabolizer
- **Ultrarapid** - Ultrarapid metabolizer
- **Reduced** - Reduced activity
- **Low** - Low activity
- **Indeterminate** - Cannot determine phenotype

### EHR Priority Levels
- **Normal/Routine/Low Risk** - Standard dosing
- **Abnormal/Priority/High Risk** - Requires dose adjustment
- **none** - No specific priority (indeterminate)

### High-Risk Diplotypes
Identified 6,564 high-risk diplotypes across all genes:
- CYP2D6: 3,849 high-risk diplotypes
- DPYD: 1,974 high-risk diplotypes
- TPMT: 418 high-risk diplotypes
- CYP2C19: 323 high-risk diplotypes
- And more...

## 💻 Usage Example

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

## 🎯 Next Steps for Integration

### Phase 1: Backend Integration (Immediate)
1. **Create `cpic_annotator.py`** in backend
   - Import `CPICAnnotator` class from example
   - Load integrated table on startup
   - Add lookup functions

2. **Update `schemas.py`**
   - Add `CPICAnnotation` model
   - Include fields: cpic_phenotype, phenotype_category, ehr_priority, validation_status

3. **Modify `main.py`**
   - Add CPIC annotation to `/api/extract-pgx-data` endpoint
   - Compare extracted phenotype with CPIC standard
   - Flag mismatches or high-risk variants

### Phase 2: API Enhancement
1. **Add validation endpoint**
   ```python
   @app.post("/api/validate-phenotype")
   async def validate_phenotype(gene, diplotype, phenotype)
   ```

2. **Add lookup endpoint**
   ```python
   @app.get("/api/cpic-lookup/{gene}/{diplotype}")
   async def cpic_lookup(gene, diplotype)
   ```

### Phase 3: Frontend Display
1. **Update PgxExtractor.js**
   - Display CPIC-standardized phenotype
   - Show validation status (✓ matches, ⚠ differs, ✗ mismatch)
   - Highlight high-risk variants in red

2. **Add CPIC badge/icon**
   - Visual indicator for CPIC-validated results
   - Tooltip with CPIC phenotype details

### Phase 4: Enhanced Features
1. **Batch annotation** - Apply CPIC standardization to all batch results
2. **Export enhancement** - Include CPIC annotations in CSV export
3. **Statistics** - Show distribution of phenotype categories
4. **Alerts** - Flag high-risk variants for clinical review

## 📁 Files Created

```
annotations/
├── CPIC translations/              # Original CPIC tables (15 files)
├── cpic_diplotype_phenotype_integrated.csv  # ✅ Integrated table (1.8 MB)
├── integrate_cpic_tables.py        # ✅ Integration script
├── example_lookup.py               # ✅ Usage examples
├── README.md                       # ✅ Documentation
└── INTEGRATION_SUMMARY.md          # ✅ This file
```

## 🧪 Testing

The integration has been tested with:
- ✅ All 15 CPIC tables successfully merged
- ✅ 27,169 diplotypes loaded
- ✅ Lookup functionality verified
- ✅ Validation logic tested
- ✅ High-risk identification working
- ✅ Gene summaries accurate

**Test Results:**
```
✅ CYP2C19 *1/*2 lookup: Intermediate Metabolizer
✅ Validation: Exact match detection working
✅ Validation: Category match detection working
✅ Validation: Mismatch detection working
✅ High-risk identification: 6,564 total found
✅ Gene summaries: All 15 genes processed correctly
```

## 📚 References

**Data Source:** CPIC (Clinical Pharmacogenetics Implementation Consortium)
- Website: https://cpicpgx.org/
- Guidelines: https://cpicpgx.org/guidelines/

**Citation:**
> Clinical Pharmacogenetics Implementation Consortium (CPIC®). 
> Available at: https://cpicpgx.org/

## 🔄 Maintenance

**To update with new CPIC data:**
```bash
cd annotations
python integrate_cpic_tables.py
```

This will regenerate the integrated file with any new tables added to `CPIC translations/` directory.

## ✅ Success Criteria Met

- [x] All 15 CPIC tables integrated into single CSV
- [x] Standardized column names across all genes
- [x] Added phenotype category extraction
- [x] Created comprehensive documentation
- [x] Provided working code examples
- [x] Tested lookup and validation functions
- [x] Identified high-risk diplotypes
- [x] Ready for backend integration

## 🎉 Summary

Successfully integrated 15 CPIC translation tables containing 27,169 diplotype-to-phenotype mappings into a single, standardized CSV file. The integrated table is ready to be used for:

1. **Standardizing** phenotypes extracted from PDF reports
2. **Validating** genotype-phenotype assignments
3. **Annotating** results with CPIC-compliant phenotypes
4. **Flagging** high-risk variants requiring clinical attention

The integration includes complete documentation, working examples, and a clear path for backend integration into the PGX Parser pipeline.

---

**Status:** ✅ Ready for integration into PGX Parser backend
**Next Action:** Implement `cpic_annotator.py` in backend and update API endpoints
