# PGX Parser - Quick Start Guide

## 🚀 Fastest Way to Run

### Option 1: Using Startup Scripts (Recommended)

```bash
# Terminal 1 - Start Backend
./start-backend.sh

# Terminal 2 - Start Frontend (in a new terminal)
./start-frontend.sh
```

### Option 2: Manual Start

```bash
# Terminal 1 - Backend
cd pgx-parser-backend-py
conda activate pgxbridge_env
uvicorn main:app --reload --port 8000

# Terminal 2 - Frontend
cd pgx-parser-ui
npm start
```

## ✅ Verify It's Working

1. **Backend Health Check:**
   ```bash
   curl http://localhost:8000/healthz
   # Should return: {"ok":true}
   ```

2. **Frontend:** Open browser to `http://localhost:3000`

3. **API Docs:** Visit `http://localhost:8000/docs`

## 📋 Prerequisites

Before running, ensure you have:

- ✅ **Conda environment:** `pgxbridge_env` (script will create if missing)
- ✅ **Node.js 18+:** Check with `node --version`
- ✅ **Azure credentials:** Set in `pgx-parser-backend-py/.env`

### Required .env Variables

Create `pgx-parser-backend-py/.env` with:

```bash
AZURE_DI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DI_KEY=your-document-intelligence-key

AZURE_OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name
AZURE_OPENAI_API_VERSION=2024-02-15-preview

ALLOWED_ORIGINS=http://localhost:3000
```

## 🧪 Quick Test

1. Open `http://localhost:3000`
2. Click **"PGX Gene Extractor"** tab
3. Enter keyword: `pharmacogenomics`
4. Upload a PGX PDF report
5. Click **"Extract PGX Data"**

**Expected Result:** Patient info + 13 genes with genotypes and metabolizer status

## 📊 Available Features

| Feature | Tab | Description |
|---------|-----|-------------|
| **Document Processor** | Tab 1 | Filter PDF pages by keyword + Azure DI analysis |
| **PGX Gene Extractor** | Tab 2 | Extract patient info + 13 PGX genes using LLM |
| **Batch Processing** | Tab 2 | Process multiple PDFs at once |
| **Similarity Scoring** | Tab 2 | Compare LLM vs Document Intelligence results |
| **CSV Export** | Tab 2 | Download batch results as CSV |

## 🎯 13 PGX Genes Extracted

- CYP2B6, CYP2C19, CYP2C9, CYP2D6
- CYP3A5, CYP4F2, DPYD, NAT2
- NUDT15, SLCO1B1, TPMT, UGT1A1, VKORC1

## 🛑 Stop Services

Press `CTRL+C` in each terminal window

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| Port 8000 in use | `lsof -ti:8000 \| xargs kill -9` |
| Port 3000 in use | `lsof -ti:3000 \| xargs kill -9` |
| Module not found | `pip install -r requirements.txt` |
| npm errors | `rm -rf node_modules && npm install` |
| Azure auth error | Check `.env` credentials |

## 📚 Full Documentation

- **Complete Testing Guide:** See `TESTING_GUIDE.md`
- **Backend README:** `pgx-parser-backend-py/README.md`
- **Frontend README:** `pgx-parser-ui/README.md`
- **API Docs:** `http://localhost:8000/docs` (when running)

## 🔗 Useful URLs

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Health Check: http://localhost:8000/healthz
