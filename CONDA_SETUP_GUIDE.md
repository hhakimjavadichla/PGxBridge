# Conda Environment Setup Guide

## 🔍 Current Situation Analysis

You have **two conda installations**:

| Installation | Version | Size | Location | Status |
|-------------|---------|------|----------|--------|
| **Miniforge3** | 25.3.1 | 5.6 GB | `/Users/hhakimjavadi/miniforge3` | Currently active (base) |
| **Anaconda3** | 23.1.0 | 36 GB | `/Users/hhakimjavadi/opt/anaconda3` | Has `pgxbridge_env` |

### Current Environment Status
- ✅ `pgxbridge_env` is **already active** in your current terminal
- ✅ All required packages are installed
- ✅ Python 3.9.23 with FastAPI, Azure, OpenAI packages

## 🎯 Recommendation: Use Miniforge3 (Modern & Lightweight)

**Why Miniforge3 is better:**
- ✅ **Newer version** (25.3.1 vs 23.1.0)
- ✅ **Much smaller** (5.6 GB vs 36 GB)
- ✅ **Faster** package resolution
- ✅ **Open source** (uses conda-forge by default)
- ✅ **Better for Apple Silicon** (M1/M2/M3 Macs)
- ✅ **Already your default** conda

## 📋 Recommended Solution: Create New Environment in Miniforge3

### Step 1: Backup Current Environment (Safety First!)

```bash
# Export current environment to a file
conda activate pgxbridge_env
conda env export > pgxbridge_env_backup.yml

# Save installed packages list
pip list > pgxbridge_env_packages.txt

# Move backups to project directory
mv pgxbridge_env_backup.yml /Users/hhakimjavadi/Library/CloudStorage/OneDrive-ChildrensHospitalLosAngeles/UF_Dropbox/pgx_reporting/azure/python/pgx-bridge_v02/
mv pgxbridge_env_packages.txt /Users/hhakimjavadi/Library/CloudStorage/OneDrive-ChildrensHospitalLosAngeles/UF_Dropbox/pgx_reporting/azure/python/pgx-bridge_v02/
```

### Step 2: Create New Environment in Miniforge3

```bash
# Deactivate current environment
conda deactivate

# Create new environment with Python 3.11 (newer than 3.9)
conda create -n pgx_parser python=3.11 -y

# Activate the new environment
conda activate pgx_parser

# Navigate to backend directory
cd /Users/hhakimjavadi/Library/CloudStorage/OneDrive-ChildrensHospitalLosAngeles/UF_Dropbox/pgx_reporting/azure/python/pgx-bridge_v02/pgx-parser-backend-py

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep -E "fastapi|uvicorn|pypdf|azure|openai"
```

### Step 3: Test the New Environment

```bash
# Test backend startup
uvicorn main:app --reload --host 10.241.1.171 --port 8010

# In browser, visit:
# http://10.241.1.171:8010/healthz
# http://10.241.1.171:8010/docs
```

### Step 4: Update Documentation

Once verified, update the environment name in your scripts and docs from `pgxbridge_env` to `pgx_parser`.

## 🔄 Rollback Plan (If Something Goes Wrong)

### Option A: Restore from Backup File

```bash
# Create environment from backup
conda env create -f pgxbridge_env_backup.yml

# Activate it
conda activate pgxbridge_env
```

### Option B: Use Anaconda3 Directly

```bash
# Initialize anaconda3 in your shell
source /Users/hhakimjavadi/opt/anaconda3/bin/activate

# Activate the existing environment
conda activate pgxbridge_env

# Start backend
cd pgx-parser-backend-py
uvicorn main:app --reload --host 10.241.1.171 --port 8010
```

### Option C: Reinstall from requirements.txt

```bash
# Create fresh environment
conda create -n pgx_parser_recovery python=3.11 -y
conda activate pgx_parser_recovery

# Install from requirements
cd pgx-parser-backend-py
pip install -r requirements.txt
```

## 📝 Quick Reference Commands

### Check Which Conda is Active
```bash
which conda
conda --version
echo $CONDA_DEFAULT_ENV
```

### List All Environments
```bash
conda env list
```

### Switch Between Conda Installations
```bash
# Use Miniforge3 (recommended)
source /Users/hhakimjavadi/miniforge3/bin/activate

# Use Anaconda3 (if needed)
source /Users/hhakimjavadi/opt/anaconda3/bin/activate
```

### Remove Old Environment (After Testing New One)
```bash
# Only do this after confirming new environment works!
conda env remove -n pgxbridge_env
```

## 🎯 Final Recommended Setup

### For This Project

**Environment Name:** `pgx_parser`  
**Conda Installation:** Miniforge3  
**Python Version:** 3.11  
**Location:** `/Users/hhakimjavadi/miniforge3/envs/pgx_parser`

### Activation Command

```bash
conda activate pgx_parser
```

This will work consistently because it's in your default conda installation (Miniforge3).

## 📊 Comparison Table

| Aspect | Keep `pgxbridge_env` (Anaconda3) | Create `pgx_parser` (Miniforge3) |
|--------|----------------------------------|----------------------------------|
| **Pros** | Already working, no changes needed | Newer Python, faster, smaller, consistent |
| **Cons** | Old Python (3.9), activation issues, large install | Need to recreate, test everything |
| **Risk** | Low (current state) | Low (can rollback easily) |
| **Long-term** | May have compatibility issues | Better for future development |
| **Recommendation** | ⚠️ Temporary solution | ✅ **Best long-term solution** |

## 🚀 Step-by-Step Migration (Recommended)

Execute these commands in order:

```bash
# 1. Backup current environment
cd /Users/hhakimjavadi/Library/CloudStorage/OneDrive-ChildrensHospitalLosAngeles/UF_Dropbox/pgx_reporting/azure/python/pgx-bridge_v02
conda activate pgxbridge_env
conda env export > pgxbridge_env_backup.yml
pip list > pgxbridge_env_packages.txt
echo "✅ Backup created"

# 2. Create new environment
conda deactivate
conda create -n pgx_parser python=3.11 -y
echo "✅ New environment created"

# 3. Install dependencies
conda activate pgx_parser
cd pgx-parser-backend-py
pip install -r requirements.txt
echo "✅ Dependencies installed"

# 4. Test it works
python --version
pip list | grep fastapi
echo "✅ Verification complete"

# 5. Test backend
uvicorn main:app --reload --host 10.241.1.171 --port 8010
# Press Ctrl+C after confirming it starts

# 6. If everything works, you're done!
echo "✅ Migration successful! Use 'conda activate pgx_parser' from now on"
```

## 📱 Update Your Workflow

After migration, update your startup commands:

### Old Way (Anaconda3):
```bash
conda activate pgxbridge_env  # ❌ Doesn't work easily
```

### New Way (Miniforge3):
```bash
conda activate pgx_parser  # ✅ Works consistently
```

## 🔒 Safety Checklist

Before removing old environment:

- [ ] New environment created successfully
- [ ] All packages installed (`pip list` shows everything)
- [ ] Backend starts without errors
- [ ] Frontend connects to backend
- [ ] Can process a test PDF
- [ ] Backup files saved (`pgxbridge_env_backup.yml` exists)
- [ ] Tested for at least 1 day

## 💾 Backup Files Location

Your backup files are saved in:
```
/Users/hhakimjavadi/Library/CloudStorage/OneDrive-ChildrensHospitalLosAngeles/UF_Dropbox/pgx_reporting/azure/python/pgx-bridge_v02/
├── pgxbridge_env_backup.yml      # Full environment specification
└── pgxbridge_env_packages.txt    # List of installed packages
```

Keep these files until you're confident the new setup works perfectly!

## 🆘 Emergency Contacts

If something goes wrong:

1. **Check this guide:** `CONDA_SETUP_GUIDE.md`
2. **Rollback:** Use Option A, B, or C above
3. **Troubleshooting:** See `TROUBLESHOOTING.md`
4. **Start fresh:** Delete and recreate environment

## 📞 Quick Help Commands

```bash
# Where am I?
echo $CONDA_DEFAULT_ENV
which python

# What's installed?
pip list

# Start over
conda deactivate
conda activate pgx_parser

# Nuclear option (start completely fresh)
conda env remove -n pgx_parser
conda create -n pgx_parser python=3.11 -y
conda activate pgx_parser
cd pgx-parser-backend-py
pip install -r requirements.txt
```

---

**Recommendation:** Follow the migration steps above to create `pgx_parser` in Miniforge3. It's the cleanest, most maintainable solution for the long term.
