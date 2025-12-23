# 🚀 START HERE - PGX Parser

**Welcome back!** This guide will get you running in 5 minutes.

## ⚡ Quick Start (3 Steps)

### Step 1: Start Backend (Terminal 1)

```bash
cd /Users/hhakimjavadi/Library/CloudStorage/OneDrive-ChildrensHospitalLosAngeles/UF_Dropbox/pgx_reporting/azure/python/pgx-bridge_v02

./start-backend.sh
```

**Expected output:**
```
✅ Starting FastAPI server on http://localhost:8000
📚 API docs available at http://localhost:8000/docs
```

### Step 2: Start Frontend (Terminal 2)

Open a **new terminal** and run:

```bash
cd /Users/hhakimjavadi/Library/CloudStorage/OneDrive-ChildrensHospitalLosAngeles/UF_Dropbox/pgx_reporting/azure/python/pgx-bridge_v02

./start-frontend.sh
```

**Expected output:**
```
✅ Starting React app on http://localhost:3000
```

Your browser should automatically open to `http://localhost:3000`

### Step 3: Test It Works

1. Go to `http://localhost:3000`
2. Click **"PGX Gene Extractor"** tab
3. Enter keyword: `pharmacogenomics`
4. Upload a PGX PDF report
5. Click **"Extract PGX Data"**

**You should see:**
- ✅ Patient information (name, DOB, etc.)
- ✅ 13 PGX genes with genotypes and metabolizer status

## 📚 Documentation Created for You

I've created comprehensive documentation:

| Document | Purpose | When to Use |
|----------|---------|-------------|
| **START_HERE.md** | This file - quickest way to get started | First time running |
| **QUICK_START.md** | Fast reference for running the app | Every time you start |
| **TESTING_GUIDE.md** | Complete testing instructions | Testing all features |
| **PROJECT_STATUS.md** | Full project overview & architecture | Understanding the system |
| **TROUBLESHOOTING.md** | Solutions to common problems | When something breaks |

### Quick Access

```bash
# View any document
cat QUICK_START.md
cat TESTING_GUIDE.md
cat PROJECT_STATUS.md
cat TROUBLESHOOTING.md
```

## 🎯 What This Project Does

**Input:** PDF reports (10-20 pages) with pharmacogenomics data

**Output:** Structured JSON with:
- Patient demographics and sample info
- 13 PGX genes (CYP2B6, CYP2C19, CYP2C9, CYP2D6, CYP3A5, CYP4F2, DPYD, NAT2, NUDT15, SLCO1B1, TPMT, UGT1A1, VKORC1)
- Genotype and metabolizer status for each gene

**Features:**
- ✅ Single file processing
- ✅ Batch processing (multiple PDFs)
- ✅ LLM-based extraction (Azure OpenAI)
- ✅ Quality scoring
- ✅ CSV export

## 🔧 If Something Goes Wrong

### Backend won't start?
```bash
cd pgx-parser-backend-py
conda activate pgxbridge_env
pip install -r requirements.txt
```

### Frontend won't start?
```bash
cd pgx-parser-ui
rm -rf node_modules
npm install
```

### Port already in use?
```bash
# Kill process on port 8000 (backend)
lsof -ti:8000 | xargs kill -9

# Kill process on port 3000 (frontend)
lsof -ti:3000 | xargs kill -9
```

### Need more help?
👉 See **TROUBLESHOOTING.md** for detailed solutions

## ✅ Verify It's Working

Run these checks:

```bash
# 1. Backend health check
curl http://localhost:8000/healthz
# Should return: {"ok":true}

# 2. Frontend is running
curl http://localhost:3000
# Should return HTML

# 3. View API documentation
open http://localhost:8000/docs
```

## 📊 Current Project Status

✅ **Production Ready**

- Backend: FastAPI with Azure AI integration
- Frontend: React with batch processing
- Features: All implemented and tested
- Documentation: Complete

## 🎓 Next Steps After Running

1. **Test with your PDFs** - Upload actual PGX reports
2. **Try batch processing** - Process multiple files at once
3. **Export results** - Download CSV of extracted data
4. **Review accuracy** - Check similarity scores
5. **Read documentation** - Understand all features

## 📞 Quick Reference

| What | Where |
|------|-------|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Health Check | http://localhost:8000/healthz |
| Backend Code | `pgx-parser-backend-py/` |
| Frontend Code | `pgx-parser-ui/` |

## 🛑 When You're Done

Press `CTRL+C` in both terminal windows to stop the servers.

---

**That's it!** You're ready to go. Start with the commands in Step 1 and Step 2 above.

For detailed testing instructions, see **TESTING_GUIDE.md**
