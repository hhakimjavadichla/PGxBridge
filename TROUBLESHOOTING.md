# PGX Parser - Troubleshooting Guide

Quick reference for common issues and solutions.

## 🔍 Quick Diagnostics

Run these commands to check system status:

```bash
# Check if backend is running
curl http://localhost:8000/healthz

# Check if frontend is running
curl http://localhost:3000

# Check conda environment
conda env list | grep pgxbridge_env

# Check Node.js version
node --version  # Should be 18+

# Check Python version
python --version  # Should be 3.11+

# Check if ports are in use
lsof -i :8000  # Backend port
lsof -i :3000  # Frontend port
```

## 🚨 Common Issues & Solutions

### 1. Backend Won't Start

#### Issue: `ModuleNotFoundError: No module named 'fastapi'`

**Cause:** Dependencies not installed

**Solution:**
```bash
cd pgx-parser-backend-py
conda activate pgxbridge_env
pip install -r requirements.txt
```

#### Issue: `Port 8000 already in use`

**Cause:** Another process is using port 8000

**Solution:**
```bash
# Find and kill the process
lsof -ti:8000 | xargs kill -9

# Or use a different port
uvicorn main:app --reload --port 8001
```

#### Issue: `Azure credentials not configured`

**Cause:** Missing or incorrect `.env` file

**Solution:**
```bash
cd pgx-parser-backend-py

# Check if .env exists
ls -la .env

# If missing, create it with required variables
cat > .env << EOF
AZURE_DI_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DI_KEY=your-key-here
AZURE_OPENAI_API_KEY=your-openai-key
AZURE_OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment
AZURE_OPENAI_API_VERSION=2024-02-15-preview
ALLOWED_ORIGINS=http://localhost:3000
EOF
```

#### Issue: `conda: command not found`

**Cause:** Conda not installed or not in PATH

**Solution:**
```bash
# Check if conda is installed
which conda

# If not found, use venv instead
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Frontend Won't Start

#### Issue: `npm: command not found`

**Cause:** Node.js/npm not installed

**Solution:**
```bash
# Install Node.js using Homebrew (Mac)
brew install node

# Or download from https://nodejs.org/
```

#### Issue: `Port 3000 already in use`

**Cause:** Another React app or process is using port 3000

**Solution:**
```bash
# Kill the process
lsof -ti:3000 | xargs kill -9

# Or set a different port
PORT=3001 npm start
```

#### Issue: `npm install` fails with errors

**Cause:** Corrupted node_modules or package-lock.json

**Solution:**
```bash
cd pgx-parser-ui

# Clean install
rm -rf node_modules package-lock.json
npm cache clean --force
npm install
```

#### Issue: `Cannot connect to backend`

**Cause:** Backend not running or wrong port

**Solution:**
```bash
# Verify backend is running
curl http://localhost:8000/healthz

# Check proxy setting in package.json
cat package.json | grep proxy
# Should show: "proxy": "http://localhost:8000"

# If backend is on different port, update package.json
```

### 3. Azure API Errors

#### Issue: `Azure API error: Unauthorized (401)`

**Cause:** Invalid or expired API key

**Solution:**
```bash
# Verify credentials in .env
cd pgx-parser-backend-py
cat .env | grep AZURE

# Check Azure portal for correct keys
# Regenerate keys if necessary
```

#### Issue: `Azure API error: Quota exceeded (429)`

**Cause:** API rate limit reached

**Solution:**
- Wait for quota to reset (usually 1 minute)
- Upgrade to higher tier in Azure portal
- Reduce request frequency

#### Issue: `File too large (413)`

**Cause:** PDF exceeds size limits

**Solution:**
- Free tier (F0): 4 MB limit
- Standard tier (S0): 500 MB limit
- Backend limit: 520 MB

**Options:**
- Compress PDF
- Split into smaller files
- Upgrade Azure tier

#### Issue: `Only first 2 pages processed`

**Cause:** Using Free tier (F0) of Azure Document Intelligence

**Solution:**
- This is expected behavior for F0 tier
- Upgrade to Standard tier (S0) for full document processing
- Or ensure PGX data is on first 2 pages

### 4. PDF Processing Errors

#### Issue: `No pages contained the keyword`

**Cause:** Keyword not found in PDF

**Solution:**
- Check spelling of keyword
- Try case-insensitive variations
- Use more common terms (e.g., "gene" instead of "pharmacogenomics")
- Verify PDF is text-based (not scanned image)

#### Issue: `Failed to extract text from PDF`

**Cause:** PDF is corrupted or image-based

**Solution:**
- Verify PDF opens correctly in PDF reader
- If scanned image, use OCR preprocessing
- Try re-exporting PDF from source

#### Issue: `Invalid file type`

**Cause:** Non-PDF file uploaded

**Solution:**
- Ensure file has .pdf extension
- Verify file is actually PDF (not renamed image)
- Check MIME type is application/pdf

### 5. LLM Extraction Errors

#### Issue: `LLM extraction failed`

**Cause:** Azure OpenAI service error or timeout

**Solution:**
```bash
# Check OpenAI configuration
cd pgx-parser-backend-py
cat .env | grep OPENAI

# Verify deployment name is correct
# Check Azure OpenAI service status
```

#### Issue: `Missing gene data`

**Cause:** LLM couldn't find data in PDF

**Solution:**
- Verify PDF contains PGX gene table
- Check keyword filters correct pages
- Try without keyword (processes all pages)
- Verify table format matches expected structure

#### Issue: `Incorrect genotypes extracted`

**Cause:** PDF format differs from training examples

**Solution:**
- Check similarity scores (should be >70%)
- Manually verify against PDF
- Report format variations for model improvement

### 6. Batch Processing Issues

#### Issue: `Batch processing stops after first file`

**Cause:** Error in first file breaks the loop

**Solution:**
- Check browser console for errors
- Verify all files are valid PDFs
- Process files individually to identify problem file

#### Issue: `CSV export is empty`

**Cause:** No successful extractions

**Solution:**
- Check individual file results for errors
- Verify at least one file processed successfully
- Check browser console for export errors

### 7. Performance Issues

#### Issue: `Processing is very slow`

**Cause:** Large PDF or slow network

**Solution:**
- Check PDF file size (compress if >10 MB)
- Verify internet connection
- Check Azure service region (closer is faster)
- Monitor backend logs for bottlenecks

#### Issue: `Browser freezes during batch processing`

**Cause:** Processing too many files at once

**Solution:**
- Process in smaller batches (5-10 files)
- Close other browser tabs
- Increase browser memory limit

### 8. Display Issues

#### Issue: `Results not showing`

**Cause:** JavaScript error or API response issue

**Solution:**
```bash
# Open browser DevTools (F12)
# Check Console tab for errors
# Check Network tab for failed requests

# Verify API response format
curl -X POST http://localhost:8000/api/extract-pgx-data \
  -F "keyword=test" \
  -F "file=@sample.pdf"
```

#### Issue: `Similarity scores not displayed`

**Cause:** Comparison not available (only LLM extraction)

**Solution:**
- This is expected when only using LLM extraction
- Document Intelligence comparison is optional feature
- Check `comparison_available` field in response

## 🔧 Advanced Troubleshooting

### Enable Debug Logging

**Backend:**
```python
# In main.py, change logging level
logging.basicConfig(level=logging.DEBUG)
```

**Frontend:**
```javascript
// In api.js, add console.log statements
console.log('API Request:', url, data);
console.log('API Response:', response);
```

### Check Backend Logs

```bash
# Run backend with verbose output
cd pgx-parser-backend-py
uvicorn main:app --reload --port 8000 --log-level debug
```

### Test API Directly

```bash
# Test health endpoint
curl -v http://localhost:8000/healthz

# Test with sample file
curl -v -X POST http://localhost:8000/api/extract-pgx-data \
  -F "keyword=test" \
  -F "file=@sample.pdf" \
  | jq '.'  # Pretty print JSON
```

### Verify Dependencies

**Backend:**
```bash
cd pgx-parser-backend-py
pip list | grep -E "fastapi|uvicorn|pypdf|azure|openai"
```

**Frontend:**
```bash
cd pgx-parser-ui
npm list react react-dom react-scripts
```

## 📞 Getting Help

### Before Asking for Help

1. ✅ Check this troubleshooting guide
2. ✅ Review error messages in terminal
3. ✅ Check browser console (F12)
4. ✅ Verify all prerequisites are met
5. ✅ Test with sample data

### Information to Provide

When reporting issues, include:

- **Error message:** Full text from terminal or console
- **Steps to reproduce:** What you did before error occurred
- **Environment:**
  - OS version: `sw_vers` (Mac) or `uname -a` (Linux)
  - Python version: `python --version`
  - Node version: `node --version`
  - Conda environment: `conda env list`
- **Logs:** Backend terminal output
- **File info:** PDF size, number of pages
- **Configuration:** Sanitized .env (remove keys)

### Useful Commands for Bug Reports

```bash
# System info
sw_vers  # Mac
uname -a  # Linux

# Python environment
python --version
pip list

# Node environment
node --version
npm --version
npm list --depth=0

# Backend status
curl http://localhost:8000/healthz
curl http://localhost:8000/docs

# Check running processes
ps aux | grep uvicorn
ps aux | grep node

# Check ports
lsof -i :8000
lsof -i :3000

# Network connectivity
ping cognitiveservices.azure.com
ping openai.azure.com
```

## ✅ Verification Checklist

After fixing issues, verify:

- [ ] Backend health check returns `{"ok": true}`
- [ ] Frontend loads at http://localhost:3000
- [ ] Can upload PDF file
- [ ] Can process single file
- [ ] Patient info extracted correctly
- [ ] All 13 genes extracted
- [ ] Batch processing works
- [ ] CSV export works
- [ ] No errors in browser console
- [ ] No errors in backend logs

## 🎯 Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Port in use | `lsof -ti:PORT \| xargs kill -9` |
| Module not found | `pip install -r requirements.txt` |
| npm errors | `rm -rf node_modules && npm install` |
| Azure auth error | Check `.env` credentials |
| Backend not running | `./start-backend.sh` |
| Frontend not running | `./start-frontend.sh` |
| Slow processing | Compress PDF, check network |
| No results | Check keyword, verify PDF format |

## 📚 Additional Resources

- **Project Documentation:** `README.md`
- **Quick Start:** `QUICK_START.md`
- **Testing Guide:** `TESTING_GUIDE.md`
- **Project Status:** `PROJECT_STATUS.md`
- **API Docs:** http://localhost:8000/docs
