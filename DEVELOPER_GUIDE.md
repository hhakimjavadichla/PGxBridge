# PGX Parser - Comprehensive Developer Guide

> **Last Updated**: January 2026  
> **Version**: 2.1  
> **Purpose**: Complete reference for developers continuing this project

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Architecture](#2-architecture)
3. [Technology Stack](#3-technology-stack)
4. [Environment Setup](#4-environment-setup)
5. [Backend Reference](#5-backend-reference)
6. [Frontend Reference](#6-frontend-reference)
7. [CPIC Integration](#7-cpic-integration)
8. [Word Report Generation](#8-word-report-generation)
9. [API Reference](#9-api-reference)
10. [Data Schemas](#10-data-schemas)
11. [File Structure](#11-file-structure)
12. [Testing](#12-testing)
13. [Troubleshooting](#13-troubleshooting)
14. [Future Development](#14-future-development)

---

## 1. Project Overview

### What is PGX Parser?

PGX Parser is a pharmacogenomics (PGx) report processing application that:

1. **Extracts patient information** from PDF reports (name, DOB, report date, etc.)
2. **Extracts gene data** for 13 standard PGx genes (genotype and metabolizer status)
3. **Annotates with CPIC standards** (phenotype validation, EHR priority, high-risk flagging)
4. **Generates Word document reports** (patient-facing and EHR-facing)
5. **Exports data as CSV** for further analysis

### Target Genes (13 Standard PGx Genes)

| Gene | Category | Clinical Relevance |
|------|----------|-------------------|
| CYP2B6 | Metabolizer | Drug metabolism |
| CYP2C9 | Metabolizer | Warfarin, NSAIDs |
| CYP2C19 | Metabolizer | Clopidogrel, PPIs |
| CYP2D6 | Metabolizer | Opioids, antidepressants |
| CYP3A5 | Metabolizer | Tacrolimus |
| CYP4F2 | Metabolizer | Warfarin |
| DPYD | Metabolizer | Fluoropyrimidines |
| NAT2 | Metabolizer | Isoniazid |
| NUDT15 | Metabolizer | Thiopurines |
| SLCO1B1 | Transporter | Statins |
| TPMT | Metabolizer | Thiopurines |
| UGT1A1 | Metabolizer | Irinotecan |
| VKORC1 | Metabolizer | Warfarin |

---

## 2. Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                           │
│                    (React.js - Port 3000)                        │
├─────────────────────────────────────────────────────────────────┤
│  PgxExtractor Component                                          │
│  ├── PDF Upload + Keyword Input                                  │
│  ├── Extract PGx Data Button                                     │
│  ├── Results Display (Patient Info + Gene Table)                 │
│  ├── CSV Export Buttons                                          │
│  └── Word Report Generation Buttons                              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼ HTTP REST API
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                             │
│                 (Python - 10.241.1.171:8010)                      │
├─────────────────────────────────────────────────────────────────┤
│  Endpoints:                                                      │
│  ├── POST /api/extract-pgx-data      → Main extraction           │
│  ├── POST /api/generate-patient-report → Patient Word doc        │
│  ├── POST /api/generate-ehr-report   → EHR Word doc              │
│  └── GET  /healthz                   → Health check              │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  Azure OpenAI   │ │  CPIC Database  │ │  Word Templates │
│  (GPT-4)        │ │  (CSV 27K rows) │ │  (.docx files)  │
│                 │ │                 │ │                 │
│  - Patient info │ │  - Phenotype    │ │  - Patient      │
│  - Gene data    │ │  - EHR Priority │ │  - EHR Note     │
│  - Extraction   │ │  - Validation   │ │                 │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### Data Flow

1. **User uploads PDF** → Frontend sends to `/api/extract-pgx-data`
2. **Backend extracts text** using `pypdf`
3. **LLM parses content** → Patient info + Gene data
4. **CPIC annotator validates** → Phenotypes, EHR priority, match status
5. **Response returned** → JSON with all extracted data
6. **User clicks report button** → Backend generates Word doc from template
7. **Word doc downloaded** → Patient or EHR format

---

## 3. Technology Stack

### Backend (Python 3.11+)

| Package | Version | Purpose |
|---------|---------|---------|
| `fastapi` | ≥0.100.0 | Web framework |
| `uvicorn` | ≥0.22.0 | ASGI server |
| `pydantic` | ≥2.0.0 | Data validation |
| `pypdf` | ≥3.0.0 | PDF text extraction |
| `python-docx` | ≥1.1.0 | Word document generation |
| `docxtpl` | ≥0.16.0 | Jinja2-based Word templating |
| `openai` | ≥1.0.0 | Azure OpenAI client |
| `pandas` | (implicit) | CPIC table processing |
| `azure-ai-documentintelligence` | ≥1.0.0 | Azure Doc Intelligence |

### Frontend (Node.js 18+)

| Package | Purpose |
|---------|---------|
| `react` | UI framework |
| `create-react-app` | Project scaffold |

### External Services

| Service | Purpose |
|---------|---------|
| Azure OpenAI (GPT-4) | LLM extraction |
| Azure Document Intelligence | OCR (optional) |

---

## 4. Environment Setup

### Prerequisites

- Python 3.11+
- Node.js 18+
- Conda (recommended: Miniforge3)

### Backend Setup

```bash
# Navigate to backend directory
cd pgx-parser-backend-py

# Create/activate conda environment
conda activate pgxbridge_env

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env

# Edit .env with your Azure credentials:
# AZURE_OPENAI_API_KEY=your_key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
# AZURE_OPENAI_API_VERSION=2024-02-15-preview
# AZURE_DOC_INTELLIGENCE_ENDPOINT=your_endpoint
# AZURE_DOC_INTELLIGENCE_KEY=your_key

# Start backend
uvicorn main:app --reload --host 10.241.1.171 --port 8010
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd pgx-parser-ui

# Install dependencies
npm install

# Start frontend
npm start
```

### Verify Installation

1. Backend health check: `http://10.241.1.171:8010/healthz`
2. Frontend: `http://localhost:3000`
3. API docs: `http://10.241.1.171:8010/docs`

---

## 5. Backend Reference

### Module Overview

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, all endpoints |
| `schemas.py` | Pydantic models for API |
| `llm_parser.py` | Azure OpenAI extraction |
| `cpic_annotator.py` | CPIC validation |
| `report_generator.py` | Word document generation |
| `pdf_filter.py` | PDF page filtering |
| `pgx_parser.py` | Regex-based parsing (legacy) |
| `patient_parser.py` | Patient info parsing (legacy) |
| `similarity_scorer.py` | LLM vs Doc Intelligence comparison |
| `azure_client.py` | Azure Doc Intelligence client |

### Key Classes

#### `AzureLLMParser` (llm_parser.py)

```python
class AzureLLMParser:
    """Azure OpenAI-based parser for medical documents."""
    
    def extract_patient_info_llm(content: str) -> PatientInfo:
        """Extract patient info from first page content."""
        
    def extract_pgx_data_llm(content: str) -> List[PgxGeneData]:
        """Extract PGX gene data from filtered page content."""
```

#### `CPICAnnotator` (cpic_annotator.py)

```python
class CPICAnnotator:
    """Singleton class for CPIC phenotype annotation."""
    
    def lookup_phenotype(gene: str, diplotype: str) -> Optional[Dict]:
        """Look up CPIC phenotype for a gene/diplotype combination."""
        
    def annotate_genes(genes: List[Dict]) -> List[Dict]:
        """Annotate list of genes with CPIC data."""
        
    def validate_phenotype(gene: str, pdf_phenotype: str, cpic_phenotype: str) -> Tuple[str, str]:
        """Validate PDF phenotype against CPIC standard."""
```

#### Report Generator Functions (report_generator.py)

```python
# Legacy functions (python-docx based)
def generate_patient_report(patient_info: Dict, pgx_genes: List[Dict]) -> bytes:
    """Generate patient-facing Word document."""
    
def generate_ehr_report(patient_info: Dict, pgx_genes: List[Dict]) -> bytes:
    """Generate EHR-facing Word document."""

# Recommended: docxtpl-based functions (better formatting preservation)
def generate_patient_report_docxtpl(patient_info: Dict, pgx_genes: List[Dict]) -> bytes:
    """Generate patient-facing Word document using Jinja2 templates."""
    
def generate_ehr_report_docxtpl(patient_info: Dict, pgx_genes: List[Dict]) -> bytes:
    """Generate EHR-facing Word document using Jinja2 templates."""
    
def get_priority_category(gene_data: Dict) -> str:
    """Categorize gene as 'priority', 'standard', or 'unknown'."""
```

---

## 6. Frontend Reference

### Component Structure

```
src/
├── App.js                    # Main app component
├── api.js                    # API helper functions
├── index.js                  # Entry point
├── components/
│   └── PgxExtractor.js       # Main extraction component
└── styles/
    ├── App.css
    └── PgxExtractor.css
```

### API Functions (api.js)

| Function | Endpoint | Returns |
|----------|----------|---------|
| `extractPgxData(keyword, file)` | POST /api/extract-pgx-data | JSON |
| `generatePatientReport(keyword, file)` | POST /api/generate-patient-report | Blob |
| `generateEhrReport(keyword, file)` | POST /api/generate-ehr-report | Blob |

### PgxExtractor Component State

```javascript
const [keyword, setKeyword] = useState('Patient Genotype');  // Search keyword
const [file, setFile] = useState(null);                       // PDF file
const [loading, setLoading] = useState(false);                // Loading state
const [result, setResult] = useState(null);                   // Extraction result
const [error, setError] = useState(null);                     // Error message
const [generatingReport, setGeneratingReport] = useState(false);      // Patient report
const [generatingEhrReport, setGeneratingEhrReport] = useState(false); // EHR report
```

### Key UI Features

1. **PDF Upload** - Single file upload
2. **Keyword Input** - Default: "Patient Genotype"
3. **Extract Button** - Triggers LLM extraction
4. **Results Display**:
   - Patient information table
   - CPIC validation summary
   - Gene table with 7 columns
5. **Export Buttons**:
   - CSV download (patient + genes)
   - Patient Report (Word)
   - EHR Note (Word)

---

## 7. CPIC Integration

### What is CPIC?

The **Clinical Pharmacogenetics Implementation Consortium (CPIC)** provides standardized guidelines for translating genotype to phenotype for drug prescribing.

### CPIC Table Structure

Location: `annotations/cpic_diplotype_phenotype_integrated.csv`

| Column | Description | Example |
|--------|-------------|---------|
| Gene | Gene name | CYP2C19 |
| Diplotype | Genotype | *1/*2 |
| Phenotype | CPIC phenotype | Intermediate Metabolizer |
| Phenotype_Category | Category | Intermediate |
| Activity_Score | Numeric score | 1.5 |
| EHR_Priority | Clinical priority | Abnormal/Priority/High Risk |

### CPIC Annotation Fields Added to Gene Data

| Field | Type | Description |
|-------|------|-------------|
| `cpic_phenotype` | string | Simplified phenotype |
| `cpic_phenotype_full` | string | Full CPIC format |
| `cpic_phenotype_category` | string | Normal/Intermediate/Poor/etc. |
| `cpic_activity_score` | string | Numeric activity score |
| `cpic_ehr_priority` | string | EHR priority level |
| `cpic_is_high_risk` | boolean | High-risk flag |
| `cpic_match_status` | string | Validation status |
| `cpic_validation_message` | string | Human-readable message |

### Match Status Values

| Status | Meaning |
|--------|---------|
| `exact_match` | PDF phenotype exactly matches CPIC |
| `category_match` | Category matches, format differs |
| `equivalent_match` | Semantically equivalent |
| `mismatch` | PDF and CPIC disagree |
| `not_found` | Diplotype not in CPIC database |

### EHR Priority Levels

| Priority | Description |
|----------|-------------|
| `Abnormal/Priority/High Risk` | Requires clinical attention |
| `Normal/Routine/Low Risk` | Standard prescribing |
| (empty) | Unknown/indeterminate |

---

## 8. Word Report Generation

### Templates Location

```
templates/
├── PGx Patient Report_04.08.25.docx   # Patient-facing template (legacy)
├── PGx_Patient_Report_jinja2.docx     # Patient-facing Jinja2 template
├── Note template.docx                  # EHR-facing template (legacy)
└── Note_template_jinja2.docx           # EHR-facing Jinja2 template
```

### Templating Approach

The application uses **docxtpl** (Jinja2-based templating) for Word document generation. This approach:

- Preserves table borders and formatting
- Uses `{{variable}}` placeholders for dynamic content
- Uses `{%tr for item in list %}` for table row loops
- Allows non-developers to edit templates in Word

### Jinja2 Template Variables

**Patient Info:**
- `{{patient_name}}` - Patient full name
- `{{date_of_birth}}` - Date of birth
- `{{report_date}}` - Report date

**Gene Lists (for table loops):**
- `priority_genes` / `high_risk_genes` - High-risk and CYP2C19 genes
- `standard_genes` - Normal/routine genes
- `unknown_genes` / `all_genes` - All other genes

### Patient Report Structure

| Table | Content | Columns |
|-------|---------|---------|
| Table 0 | Patient info | Name, DOB, Lab, Dates |
| Table 3 | High-risk + CYP2C19 | Gene, Genotype, Phenotype, Medications |
| Table 4 | All genes | Gene, Genotype, Phenotype |

### EHR Report Structure

| Table | Content | Criteria |
|-------|---------|----------|
| Table 0 | Patient info | Name, DOB, MRN, Insurance |
| Table 1 | Priority results | High-risk OR CYP2C19 |
| Table 2 | Standard results | Normal/Routine/Low Risk |
| Table 3 | Unknown results | Empty/unknown priority |

### Gene Categorization Logic

```python
def get_priority_category(gene_data: Dict) -> str:
    """
    Returns:
        'priority' - Table 1 (high-risk + all CYP2C19)
        'standard' - Table 2 (normal/routine/low risk)
        'unknown'  - Table 3 (empty/indeterminate priority)
    """
    gene = gene_data.get("gene", "").upper()
    ehr_priority = (gene_data.get("cpic_ehr_priority", "") or "").lower()
    
    # All CYP2C19 results go to Priority
    if "CYP2C19" in gene:
        return "priority"
    
    # Check for high-risk (must check before "normal" due to "abnormal")
    if "abnormal" in ehr_priority or "high risk" in ehr_priority:
        return "priority"
    
    # Check for normal/routine/low risk
    if ehr_priority.startswith("normal") or "routine" in ehr_priority:
        return "standard"
    
    # Everything else is unknown
    return "unknown"
```

### Medication Examples

Located in `report_generator.py`:

```python
MEDICATION_EXAMPLES = {
    "CYP2B6": "Infectious Diseases: efavirenz",
    "CYP2C19": "Cardiology: clopidogrel (Plavix); Gastroenterology: ...",
    "CYP2D6": "Cardiology: flecainide; Pain Management: codeine, tramadol",
    # ... etc
}
```

---

## 9. API Reference

### POST /api/extract-pgx-data

**Purpose**: Extract patient info and gene data from PDF

**Request**:
```
Content-Type: multipart/form-data

keyword: string (required) - Keyword in PGx table pages
file: File (required) - PDF file
```

**Response** (`PgxExtractResponse`):
```json
{
  "meta": {
    "original_filename": "report.pdf",
    "keyword": "Patient Genotype",
    "matched_pages": [3, 4],
    "matched_pages_count": 2
  },
  "llm_extraction": {
    "patient_info": {
      "patient_name": "John Doe",
      "date_of_birth": "Jan 1, 1990",
      "report_date": "Dec 1, 2024"
    },
    "pgx_genes": [
      {
        "gene": "CYP2C19",
        "genotype": "*1/*2",
        "metabolizer_status": "Intermediate Metabolizer",
        "cpic_phenotype": "Intermediate Metabolizer",
        "cpic_ehr_priority": "Abnormal/Priority/High Risk",
        "cpic_is_high_risk": true,
        "cpic_match_status": "exact_match"
      }
    ],
    "extraction_method": "azure_openai_gpt4"
  },
  "cpic_summary": {
    "total_genes": 13,
    "cpic_found": 12,
    "high_risk_count": 3,
    "exact_matches": 10,
    "match_rate": 83.3
  }
}
```

### POST /api/generate-patient-report

**Purpose**: Generate patient-facing Word document

**Request**: Same as extract-pgx-data

**Response**: 
```
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="PGx_Report_John_Doe.docx"
```

### POST /api/generate-ehr-report

**Purpose**: Generate EHR-facing Word document

**Request**: Same as extract-pgx-data

**Response**: 
```
Content-Type: application/vnd.openxmlformats-officedocument.wordprocessingml.document
Content-Disposition: attachment; filename="PGx_EHR_Note_John_Doe.docx"
```

### GET /healthz

**Purpose**: Health check

**Response**:
```json
{"ok": true}
```

---

## 10. Data Schemas

### PatientInfo

```python
class PatientInfo(BaseModel):
    # Table 1 fields
    patient_name: Optional[str] = None
    date_of_birth: Optional[str] = None
    test: Optional[str] = None
    report_date: Optional[str] = None
    report_id: Optional[str] = None
    
    # Table 2 fields
    cohort: Optional[str] = None
    sample_type: Optional[str] = None
    sample_collection_date: Optional[str] = None
    sample_received_date: Optional[str] = None
    processed_date: Optional[str] = None
    ordering_clinician: Optional[str] = None
    npi: Optional[str] = None
    indication_for_testing: Optional[str] = None
```

### PgxGeneData

```python
class PgxGeneData(BaseModel):
    gene: str
    genotype: str
    metabolizer_status: str
    
    # CPIC annotation fields
    cpic_phenotype: Optional[str] = None
    cpic_phenotype_full: Optional[str] = None
    cpic_phenotype_category: Optional[str] = None
    cpic_activity_score: Optional[str] = None
    cpic_ehr_priority: Optional[str] = None
    cpic_is_high_risk: Optional[bool] = False
    cpic_match_status: Optional[str] = None
    cpic_validation_message: Optional[str] = None
```

### CPICSummary

```python
class CPICSummary(BaseModel):
    total_genes: int
    cpic_found: int
    cpic_not_found: int
    high_risk_count: int
    exact_matches: int
    mismatches: int
    match_rate: float
```

---

## 11. File Structure

```
pgx-bridge_v02/
├── README.md                          # Quick start guide
├── DEVELOPER_GUIDE.md                 # This document
├── CPIC_INTEGRATION_GUIDE.md          # CPIC details
├── FRONTEND_CPIC_UPDATE.md            # Frontend CPIC display
├── FOLDER_BATCH_PROCESSOR.md          # Batch processing
├── TESTING_GUIDE.md                   # Testing instructions
├── TROUBLESHOOTING.md                 # Common issues
│
├── pgx-parser-backend-py/             # Python backend
│   ├── main.py                        # FastAPI endpoints
│   ├── schemas.py                     # Pydantic models
│   ├── llm_parser.py                  # Azure OpenAI
│   ├── cpic_annotator.py              # CPIC validation
│   ├── report_generator.py            # Word documents
│   ├── pdf_filter.py                  # PDF utilities
│   ├── pgx_parser.py                  # Regex parsing
│   ├── patient_parser.py              # Patient info
│   ├── similarity_scorer.py           # Comparison
│   ├── azure_client.py                # Azure Doc Intel
│   ├── requirements.txt               # Dependencies
│   └── .env                           # Environment vars
│
├── pgx-parser-ui/                     # React frontend
│   ├── src/
│   │   ├── App.js
│   │   ├── api.js                     # API functions
│   │   ├── components/
│   │   │   └── PgxExtractor.js        # Main component
│   │   └── styles/
│   │       └── PgxExtractor.css
│   ├── package.json
│   └── .env
│
├── annotations/                        # CPIC data
│   └── cpic_diplotype_phenotype_integrated.csv
│
├── templates/                          # Word templates
│   ├── PGx Patient Report_04.08.25.docx  # Legacy patient template
│   ├── PGx_Patient_Report_jinja2.docx    # Jinja2 patient template
│   ├── Note template.docx                 # Legacy EHR template
│   └── Note_template_jinja2.docx          # Jinja2 EHR template
│
└── out/                                # Generated outputs
```

---

## 12. Testing

### Backend Testing

```bash
cd pgx-parser-backend-py

# Test CPIC integration
python test_cpic_integration.py

# Test with sample PDF
curl -X POST "http://10.241.1.171:8010/api/extract-pgx-data" \
  -F "keyword=Patient Genotype" \
  -F "file=@sample.pdf"
```

### Frontend Testing

1. Start backend and frontend
2. Upload a PGx report PDF
3. Verify:
   - Patient info extracted correctly
   - All 13 genes displayed
   - CPIC validation summary accurate
   - CSV export works
   - Word reports generate correctly

### Verify Word Reports

```python
from docx import Document

# Check patient report
doc = Document('out/PGx_Report_Patient.docx')
for table in doc.tables:
    print(f"Table: {len(table.rows)} rows")
```

---

## 13. Troubleshooting

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| "Azure OpenAI not configured" | Missing env vars | Check `.env` file |
| CPIC table not found | Wrong path | Verify `annotations/` folder |
| Word template not found | Wrong path | Check `templates/` folder |
| Empty gene table | Keyword mismatch | Try different keyword |
| CORS error | Backend not running | Start backend on 10.241.1.171:8010 |

### Debug Logging

```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
```

### Check CPIC Coverage

```python
from cpic_annotator import get_cpic_annotator
annotator = get_cpic_annotator()
result = annotator.lookup_phenotype("CYP2C19", "*1/*2")
print(result)
```

---

## 14. Future Development

### Potential Enhancements

1. **Batch Report Generation** - Generate Word docs for multiple patients
2. **PDF Template Support** - Support different lab report formats
3. **Drug Interaction Warnings** - Cross-reference with medication lists
4. **Database Storage** - Persist results for analytics
5. **User Authentication** - Multi-user support
6. **FHIR Integration** - Export to EHR systems
7. **Audit Logging** - Track all extractions
8. **Custom Templates** - User-configurable Word templates

### Code Quality

1. Add unit tests for all modules
2. Implement integration tests
3. Add type hints throughout
4. Set up CI/CD pipeline
5. Add code coverage reporting

### Performance

1. Cache CPIC lookups (already implemented)
2. Optimize PDF parsing
3. Add request queuing for batch processing
4. Consider async processing for large files

---

## Appendix A: Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `AZURE_OPENAI_API_KEY` | Yes | Azure OpenAI API key |
| `AZURE_OPENAI_ENDPOINT` | Yes | Azure OpenAI endpoint URL |
| `AZURE_OPENAI_DEPLOYMENT_NAME` | Yes | GPT-4 deployment name |
| `AZURE_OPENAI_API_VERSION` | No | API version (default: 2024-02-15-preview) |
| `AZURE_DOC_INTELLIGENCE_ENDPOINT` | No | Doc Intelligence endpoint |
| `AZURE_DOC_INTELLIGENCE_KEY` | No | Doc Intelligence key |
| `ALLOWED_ORIGINS` | No | CORS origins (default: http://localhost:3000) |

---

## Appendix B: Conda Environment

```bash
# Create environment
conda create -n pgxbridge_env python=3.11

# Activate
conda activate pgxbridge_env

# Install packages
pip install -r requirements.txt
```

---

## Appendix C: Quick Reference Card

```
# Start Backend
cd pgx-parser-backend-py && uvicorn main:app --reload --host 10.241.1.171 --port 8010

# Start Frontend  
cd pgx-parser-ui && npm start

# Health Check
curl http://10.241.1.171:8010/healthz

# Extract Data (curl)
curl -X POST http://10.241.1.171:8010/api/extract-pgx-data \
  -F "keyword=Patient Genotype" \
  -F "file=@report.pdf"

# Generate Patient Report (curl)
curl -X POST http://10.241.1.171:8010/api/generate-patient-report \
  -F "keyword=Patient Genotype" \
  -F "file=@report.pdf" \
  -o patient_report.docx

# Generate EHR Report (curl)
curl -X POST http://10.241.1.171:8010/api/generate-ehr-report \
  -F "keyword=Patient Genotype" \
  -F "file=@report.pdf" \
  -o ehr_report.docx
```

---

*This guide was generated to help the next development team understand and continue building the PGX Parser application.*
