# PGX Parser - Testing Guide

This guide will help you run and test all functionalities of the PGX Parser project.

## Prerequisites Checklist

- [x] Python 3.11+ installed
- [x] Node.js 18+ installed
- [ ] Azure Document Intelligence credentials
- [ ] Azure OpenAI credentials (for LLM extraction)
- [ ] Sample PGX PDF reports for testing

## Step 1: Backend Setup

### 1.1 Activate Conda Environment

```bash
conda activate pgxbridge_env
```

If the environment doesn't exist, create it:
```bash
conda create -n pgxbridge_env python=3.11
conda activate pgxbridge_env
```

### 1.2 Navigate to Backend Directory

```bash
cd pgx-parser-backend-py
```

### 1.3 Install Dependencies

```bash
pip install -r requirements.txt
```

### 1.4 Configure Environment Variables

Check if `.env` file exists and has the required credentials:

```bash
cat .env
```

Required environment variables:
```bash
# Azure Document Intelligence
AZURE_DI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DI_KEY=your-api-key-here

# Azure OpenAI (for LLM extraction)
AZURE_OPENAI_API_KEY=your-openai-key-here
AZURE_OPENAI_ENDPOINT=https://your-openai-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000
```

If `.env` doesn't exist, create it with your credentials.

### 1.5 Start the Backend Server

```bash
uvicorn main:app --reload --port 8000
```

Expected output:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

### 1.6 Verify Backend is Running

Open a new terminal and test the health endpoint:

```bash
curl http://localhost:8000/healthz
```

Expected response:
```json
{"ok":true}
```

View API documentation:
```bash
open http://localhost:8000/docs
```

## Step 2: Frontend Setup

### 2.1 Open New Terminal

Keep the backend running and open a new terminal window.

### 2.2 Navigate to Frontend Directory

```bash
cd pgx-parser-ui
```

### 2.3 Install Dependencies

```bash
npm install
```

### 2.4 Start the Frontend

```bash
npm start
```

Expected output:
```
Compiled successfully!

You can now view pgx-parser-ui in the browser.

  Local:            http://localhost:3000
  On Your Network:  http://192.168.x.x:3000
```

The app should automatically open in your browser at `http://localhost:3000`.

## Step 3: Testing Functionalities

### 3.1 Test Document Processor (Basic PDF Processing)

This feature filters PDF pages by keyword and analyzes them with Azure Document Intelligence.

**Steps:**
1. Click on the **"Document Processor"** tab
2. Enter a keyword (e.g., "pharmacogenomics" or "genotype")
3. Upload a PDF file
4. Click **"Process PDF"**

**Expected Results:**
- Shows number of pages that matched the keyword
- Displays Azure Document Intelligence analysis results
- Shows extracted text, tables, and layout information

**What it tests:**
- PDF keyword filtering
- Azure Document Intelligence integration
- Page extraction and filtering

### 3.2 Test PGX Gene Extractor (LLM-based Extraction)

This feature extracts structured PGX gene data using Azure OpenAI LLM.

**Steps:**
1. Click on the **"PGX Gene Extractor"** tab
2. Enter a keyword that appears in PGX table pages (e.g., "pharmacogenomics")
3. Upload a PGX PDF report
4. Click **"Extract PGX Data"**

**Expected Results:**
- **Patient Information Section:**
  - Patient Name
  - Date of Birth
  - Report Date
  - Report ID
  - Sample Type
  - Ordering Clinician
  - NPI
  - Indication for Testing

- **PGX Gene Data Table** (13 genes):
  - Gene names: CYP2B6, CYP2C19, CYP2C9, CYP2D6, CYP3A5, CYP4F2, DPYD, NAT2, NUDT15, SLCO1B1, TPMT, UGT1A1, VKORC1
  - Genotype for each gene
  - Metabolizer status for each gene

**What it tests:**
- LLM-based extraction
- Patient information parsing
- PGX gene data extraction
- Structured data output

### 3.3 Test Batch Processing

This feature processes multiple PDF files simultaneously.

**Steps:**
1. In the **"PGX Gene Extractor"** tab
2. Check the **"Enable Batch Processing"** checkbox
3. Upload multiple PDF files
4. Click **"Process Batch"**

**Expected Results:**
- Progress indicator showing "Processing X of Y files..."
- Individual result cards for each patient
- Success/failure status for each file
- Expandable details showing full patient info and gene data
- **"Export All Results"** button to download CSV

**What it tests:**
- Multiple file handling
- Sequential processing
- Progress tracking
- CSV export functionality
- Error handling per file

### 3.4 Test Similarity Scoring

If both extraction methods are available, the system compares results.

**Expected Results:**
- **Overall Similarity Scores:**
  - Patient Info Similarity: X%
  - Gene Data Similarity: Y%
  
- **Color-coded scores:**
  - 🟢 Green: ≥90% similarity (excellent match)
  - 🟡 Yellow: ≥70% similarity (good match)
  - 🔴 Red: <70% similarity (needs review)

**What it tests:**
- Comparison between LLM and Document Intelligence
- Field-by-field similarity calculation
- Quality assessment

## Step 4: API Testing with cURL

### 4.1 Test Health Check

```bash
curl http://localhost:8000/healthz
```

### 4.2 Test Document Processing

```bash
curl -X POST http://localhost:8000/api/process-document \
  -F "keyword=pharmacogenomics" \
  -F "file=@/path/to/your/sample.pdf"
```

### 4.3 Test PGX Data Extraction

```bash
curl -X POST http://localhost:8000/api/extract-pgx-data \
  -F "keyword=pharmacogenomics" \
  -F "file=@/path/to/your/pgx_report.pdf"
```

## Step 5: Troubleshooting

### Backend Issues

**Issue:** `ModuleNotFoundError`
```bash
# Solution: Reinstall dependencies
pip install -r requirements.txt
```

**Issue:** `Azure credentials not configured`
```bash
# Solution: Check .env file has correct credentials
cat .env
```

**Issue:** `Port 8000 already in use`
```bash
# Solution: Kill existing process or use different port
lsof -ti:8000 | xargs kill -9
# Or run on different port
uvicorn main:app --reload --port 8001
```

### Frontend Issues

**Issue:** `npm install` fails
```bash
# Solution: Clear cache and reinstall
rm -rf node_modules package-lock.json
npm install
```

**Issue:** `Port 3000 already in use`
```bash
# Solution: Kill existing process
lsof -ti:3000 | xargs kill -9
```

**Issue:** Cannot connect to backend
```bash
# Solution: Verify backend is running on port 8000
curl http://localhost:8000/healthz
# Check proxy setting in package.json
cat package.json | grep proxy
```

### Azure API Issues

**Issue:** `Azure API error: Unauthorized`
- Check your Azure credentials in `.env`
- Verify the endpoint URL is correct
- Ensure API key is valid and not expired

**Issue:** `File too large`
- Free tier (F0): 4 MB limit
- Standard tier (S0): 500 MB limit
- Backend enforces 520 MB limit

**Issue:** `Only first 2 pages processed`
- This is expected with Free tier (F0)
- Upgrade to Standard tier (S0) for full document processing

## Step 6: Test Data Requirements

### Sample PGX PDF Structure

Your test PDFs should contain:

**Page 1 - Patient Information:**
- Patient demographics table
- Sample information
- Ordering clinician details

**Pages 2-3 - PGX Gene Table:**
- Table with columns: Gene, Genotype, Metabolizer Status
- All 13 genes listed
- Keyword (e.g., "pharmacogenomics") present on these pages

### Creating Test Cases

1. **Single file test:** One valid PGX report
2. **Batch test:** 3-5 PGX reports
3. **Error test:** Non-PDF file (should fail gracefully)
4. **Large file test:** PDF near size limit
5. **Missing data test:** PDF without complete gene data

## Step 7: Monitoring and Logs

### Backend Logs

Watch backend logs in the terminal where `uvicorn` is running:
```bash
# You'll see:
INFO:     Found X pages with keyword 'pharmacogenomics': [1, 2]
INFO:     Successfully extracted patient information (LLM)
INFO:     Successfully extracted PGX data (LLM)
```

### Frontend Console

Open browser DevTools (F12) and check Console tab for:
- API request/response logs
- Error messages
- Network activity

## Step 8: Stopping the Services

### Stop Backend
Press `CTRL+C` in the backend terminal

### Stop Frontend
Press `CTRL+C` in the frontend terminal

### Deactivate Conda Environment
```bash
conda deactivate
```

## Quick Reference Commands

```bash
# Start everything
cd pgx-parser-backend-py && conda activate pgxbridge_env && uvicorn main:app --reload --port 8000
# In new terminal:
cd pgx-parser-ui && npm start

# Check if services are running
curl http://localhost:8000/healthz  # Backend
curl http://localhost:3000          # Frontend

# View API docs
open http://localhost:8000/docs

# View logs
tail -f backend.log  # If logging to file
```

## Success Criteria

✅ Backend health check returns `{"ok": true}`  
✅ Frontend loads at `http://localhost:3000`  
✅ Can upload and process PDF files  
✅ Patient information extracted correctly  
✅ All 13 PGX genes extracted with genotype and metabolizer status  
✅ Batch processing handles multiple files  
✅ Export to CSV works  
✅ Error messages are clear and helpful  

## Next Steps

After successful testing:
1. Review extracted data accuracy
2. Test with various PDF formats
3. Validate similarity scoring
4. Test error handling with invalid inputs
5. Performance testing with large batches
