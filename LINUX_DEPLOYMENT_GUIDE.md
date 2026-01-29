# PGX Parser - Linux Server Deployment Guide

> **Purpose**: Complete guide for deploying PGX Parser to a remote Linux server  
> **Target OS**: Ubuntu 20.04/22.04, CentOS/RHEL 8+, or HPC Cluster  
> **Two Paths**: (A) Standard Server with sudo, (B) HPC/No-sudo with conda/mamba

---

## Table of Contents

1. [Files to Transfer](#1-files-to-transfer)
2. [HPC Deployment (No Sudo Required)](#2-hpc-deployment-no-sudo-required) ⭐ **Start Here if on HPC**
3. [Standard Server Prerequisites](#3-standard-server-prerequisites)
4. [System Package Installation (Sudo Required)](#4-system-package-installation-sudo-required)
5. [Python Environment Setup](#5-python-environment-setup)
6. [Node.js Setup](#6-nodejs-setup)
7. [Project Configuration](#7-project-configuration)
8. [Starting the Application](#8-starting-the-application)
9. [Running as a Service (Sudo Required)](#9-running-as-a-service-sudo-required)
10. [Nginx Reverse Proxy (Sudo Required)](#10-nginx-reverse-proxy-sudo-required)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Files to Transfer

### ✅ Files TO TRANSFER

```
pgx-bridge_v02/
├── .gitignore                     # Git ignore rules
├── README.md                      # Quick start guide
├── DEVELOPER_GUIDE.md             # Comprehensive docs
├── *.md                           # All documentation files
│
├── pgx-parser-backend-py/         # Backend Python code
│   ├── *.py                       # All Python files
│   ├── requirements.txt           # Python dependencies
│   └── .env.example               # Environment template (NOT .env)
│
├── pgx-parser-ui/                 # Frontend React code
│   ├── src/                       # All source files
│   ├── public/                    # Public assets
│   ├── package.json               # Node dependencies
│   ├── package-lock.json          # Dependency lock
│   └── .env.example               # Environment template
│
├── annotations/                   # CPIC annotation data
│   ├── cpic_diplotype_phenotype_integrated.csv  # Main CPIC table
│   ├── README.md
│   └── *.py                       # Helper scripts
│
├── templates/                     # Word document templates
│   ├── PGx Patient Report_04.08.25.docx
│   └── Note template.docx
│
├── start-backend.sh               # Backend startup script
├── start-frontend.sh              # Frontend startup script
├── pgxbridge_env_backup.yml       # Conda environment backup
└── pgxbridge_env_packages.txt     # Python package list
```

### ❌ Files NOT TO TRANSFER

```
# DO NOT transfer these (contain patient data or temp files):
out/                               # Generated patient reports
*.pdf                              # Patient PDF files
PGx_Report_*.docx                  # Generated patient reports
PGx_EHR_Note_*.docx               # Generated EHR notes
*_patient.csv                      # Patient data CSVs
*_genes.csv                        # Gene data CSVs
__pycache__/                       # Python cache
node_modules/                      # Node packages (reinstall on server)
.env                               # Local environment vars (create new on server)
*.log                              # Log files
```

### Transfer Methods

**Option 1: Git Clone (Recommended)**
```bash
# On remote server
git clone https://github.com/hhakimjavadichla/PGxBridge.git pgx-bridge_v02
cd pgx-bridge_v02
```

**Option 2: SCP/RSYNC**
```bash
# From local machine
rsync -avz --exclude='out/' --exclude='node_modules/' --exclude='__pycache__/' \
  --exclude='.env' --exclude='*.pdf' --exclude='*.log' \
  pgx-bridge_v02/ user@server:/path/to/pgx-bridge_v02/
```

**Option 3: Archive Transfer**
```bash
# On local machine - create archive
tar -czf pgx-bridge_v02.tar.gz \
  --exclude='out' \
  --exclude='node_modules' \
  --exclude='__pycache__' \
  --exclude='.env' \
  --exclude='*.pdf' \
  --exclude='*.log' \
  pgx-bridge_v02/

# Transfer
scp pgx-bridge_v02.tar.gz user@server:/path/

# On remote server - extract
tar -xzf pgx-bridge_v02.tar.gz
```

---

## 2. HPC Deployment (No Sudo Required)

⭐ **Use this section if you're deploying on an HPC cluster without sudo access.**

### Prerequisites

| Component | Requirement |
|-----------|-------------|
| Environment | HPC cluster with user account |
| Package Manager | conda, mamba, or pip available |
| Disk Space | 10GB free in home directory |
| Network | Internet access (or module system) |

### Step 1: Transfer Files to HPC

```bash
# From your local machine
scp pgx-bridge_v02.tar.gz username@hpc-login-node:/home/username/

# Or use rsync
rsync -avz --exclude='out/' --exclude='node_modules/' \
  pgx-bridge_v02/ username@hpc-login-node:~/pgx-bridge_v02/

# SSH to HPC
ssh username@hpc-login-node
cd ~/pgx-bridge_v02
```

### Step 2: Set Up Conda/Mamba Environment

**Option A: Using Mamba (Faster, Recommended)**

```bash
# Load mamba module (if available)
module load mamba  # or module load conda

# Create environment with all dependencies
mamba create -n pgxbridge python=3.11 nodejs=18 -y

# Activate environment
mamba activate pgxbridge

# Install Python packages
cd pgx-parser-backend-py
pip install -r requirements.txt

# Install Node.js packages
cd ../pgx-parser-ui
npm install
```

**Option B: Using Conda**

```bash
# Load conda module (if not already in PATH)
module load anaconda  # or module load miniconda

# Create environment
conda create -n pgxbridge python=3.11 -y

# Activate environment
conda activate pgxbridge

# Install Node.js via conda
conda install -c conda-forge nodejs=18 -y

# Install Python packages
cd ~/pgx-bridge_v02/pgx-parser-backend-py
pip install -r requirements.txt

# Install Node.js packages
cd ~/pgx-bridge_v02/pgx-parser-ui
npm install
```

**Option C: Using Existing Python + Pip Only**

```bash
# If HPC has Python 3.11+ already loaded
module load python/3.11  # Check available: module avail python

# Create virtual environment
cd ~/pgx-bridge_v02/pgx-parser-backend-py
python -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt

# For Node.js, you'll need to install via conda or request from admin
# If Node.js is available as a module:
module load nodejs/18
cd ~/pgx-bridge_v02/pgx-parser-ui
npm install
```

### Step 3: Configure Environment

```bash
# Backend configuration
cd ~/pgx-bridge_v02/pgx-parser-backend-py
cp .env.example .env
nano .env  # or vi .env

# Add your Azure credentials:
# AZURE_OPENAI_API_KEY=your_key
# AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
# AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
# ALLOWED_ORIGINS=http://localhost:3000

# Create output directory
mkdir -p ~/pgx-bridge_v02/out
```

### Step 4: Start Services on HPC

**Important**: HPC login nodes typically don't allow long-running processes. You have two options:

**Option A: Interactive Session (Compute Node)**

```bash
# Request interactive session (adjust based on your HPC)
srun --pty --time=4:00:00 --cpus-per-task=2 --mem=8G bash

# Or using qsub/qlogin (SGE/PBS)
qlogin -l h_rt=4:00:00 -pe smp 2 -l mem=8G

# Once on compute node, activate environment
conda activate pgxbridge  # or source venv/bin/activate

# Start backend (terminal 1 or use screen/tmux)
cd ~/pgx-bridge_v02/pgx-parser-backend-py
uvicorn main:app --host 10.241.1.171 --port 8010 &

# Start frontend (terminal 2 or in background)
cd ~/pgx-bridge_v02/pgx-parser-ui
npm start &

# Note the compute node hostname
hostname  # e.g., compute-node-042
```

**Option B: Submit as Batch Job**

Create `~/pgx-bridge_v02/run_backend.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=pgx-backend
#SBATCH --time=8:00:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=8G
#SBATCH --output=backend-%j.log

# Adjust for your HPC scheduler (SLURM, PBS, SGE)

# Load environment
source ~/.bashrc
conda activate pgxbridge

# Start backend
cd ~/pgx-bridge_v02/pgx-parser-backend-py
uvicorn main:app --host 10.241.1.171 --port 8010
```

Create `~/pgx-bridge_v02/run_frontend.sh`:

```bash
#!/bin/bash
#SBATCH --job-name=pgx-frontend
#SBATCH --time=8:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --output=frontend-%j.log

source ~/.bashrc
conda activate pgxbridge

cd ~/pgx-bridge_v02/pgx-parser-ui
npm start
```

Submit jobs:

```bash
sbatch run_backend.sh
sbatch run_frontend.sh

# Check job status
squeue -u $USER

# Check logs
tail -f backend-*.log
tail -f frontend-*.log
```

### Step 5: Access the Application

**From Your Local Machine (SSH Tunneling):**

```bash
# Find the compute node hostname from job output
# Let's say backend is on compute-042 and frontend on compute-043

# Create SSH tunnels
ssh -L 8000:compute-042:8000 -L 3000:compute-043:3000 username@hpc-login-node

# Now access from your browser:
# Frontend: http://localhost:3000
# Backend: http://10.241.1.171:8010
# API Docs: http://10.241.1.171:8010/docs
```

**Alternative: Port Forwarding Through Login Node**

```bash
# On HPC, forward from compute node to login node
ssh -L 8000:10.241.1.171:8010 -L 3000:localhost:3000 username@compute-042 -N &

# Then from local machine
ssh -L 8000:10.241.1.171:8010 -L 3000:localhost:3000 username@hpc-login-node
```

### Step 6: Using Screen/Tmux (Persistent Sessions)

For long-running sessions:

```bash
# Start screen session
screen -S pgxparser

# Or tmux
tmux new -s pgxparser

# Split into two panes (Ctrl+a |  for screen, or Ctrl+b % for tmux)

# Terminal 1: Backend
conda activate pgxbridge
cd ~/pgx-bridge_v02/pgx-parser-backend-py
uvicorn main:app --host 10.241.1.171 --port 8010

# Terminal 2: Frontend
conda activate pgxbridge
cd ~/pgx-bridge_v02/pgx-parser-ui
npm start

# Detach: Ctrl+a d (screen) or Ctrl+b d (tmux)
# Reattach: screen -r pgxparser  or  tmux attach -t pgxparser
```

### HPC-Specific Troubleshooting

| Issue | Solution |
|-------|----------|
| "Cannot bind to port" | Port may be in use; try different port: `--port 8001` |
| "Module not found" | Check available modules: `module avail`, load needed ones |
| "Login node restrictions" | Request interactive session or submit batch job |
| "No internet on compute nodes" | Install packages on login node, or use offline conda channels |
| "Permission denied" | All files should be in your home directory (`~/`) |
| "Node.js not available" | Install via conda: `conda install -c conda-forge nodejs` |

### Quick Reference for HPC

```bash
# Activate environment
conda activate pgxbridge

# Start backend (interactive node)
cd ~/pgx-bridge_v02/pgx-parser-backend-py
uvicorn main:app --host 10.241.1.171 --port 8010

# Start frontend (interactive node)  
cd ~/pgx-bridge_v02/pgx-parser-ui
npm start

# SSH tunnel from local machine
ssh -L 8000:compute-node:8000 -L 3000:compute-node:3000 user@hpc

# Submit batch job
sbatch run_backend.sh
```

---

## 3. Standard Server Prerequisites

⚠️ **This section requires sudo access. If on HPC without sudo, use Section 2 above.**

### Minimum Requirements

| Component | Requirement |
|-----------|-------------|
| OS | Ubuntu 20.04+, CentOS 8+, or RHEL 8+ |
| CPU | 2+ cores |
| RAM | 4GB minimum, 8GB recommended |
| Disk | 10GB free space |
| Network | Internet access for package installation |
| Permissions | sudo access required |

---

## 3. System Package Installation

### Ubuntu/Debian

```bash
# Update package list
sudo apt update

# Install Python 3.11
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Install Node.js 18.x
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# Install build tools (required for some Python packages)
sudo apt install -y build-essential gcc g++ make

# Install Git (if not already installed)
sudo apt install -y git

# Optional: Install Nginx for reverse proxy
sudo apt install -y nginx
```

### CentOS/RHEL

```bash
# Enable EPEL repository
sudo dnf install -y epel-release

# Install Python 3.11
sudo dnf install -y python3.11 python3.11-devel python3.11-pip

# Install Node.js 18.x
curl -fsSL https://rpm.nodesource.com/setup_18.x | sudo bash -
sudo dnf install -y nodejs

# Install build tools
sudo dnf groupinstall -y "Development Tools"

# Install Git
sudo dnf install -y git

# Optional: Install Nginx
sudo dnf install -y nginx
```

### Verify Installations

```bash
python3.11 --version    # Should show 3.11.x
node --version          # Should show v18.x.x
npm --version           # Should show 9.x.x or 10.x.x
git --version           # Should show git version
```

---

## 4. Python Environment Setup

### Option A: Using venv (Recommended for Linux)

```bash
cd pgx-bridge_v02/pgx-parser-backend-py

# Create virtual environment
python3.11 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt

# Verify installation
python -c "import fastapi; print('FastAPI installed:', fastapi.__version__)"
```

### Option B: Using Conda/Miniforge

```bash
# Install Miniforge (if not already installed)
wget https://github.com/conda-forge/miniforge/releases/latest/download/Miniforge3-Linux-x86_64.sh
bash Miniforge3-Linux-x86_64.sh -b -p $HOME/miniforge3
source $HOME/miniforge3/bin/activate

# Create environment from backup
conda env create -f pgxbridge_env_backup.yml -n pgxbridge_env

# Or create fresh environment
conda create -n pgxbridge_env python=3.11
conda activate pgxbridge_env
pip install -r pgx-parser-backend-py/requirements.txt
```

### Required Python Packages

From `requirements.txt`:
```
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
pypdf>=3.0.0
python-docx>=1.1.0
openai>=1.0.0
pandas
python-multipart
python-dotenv
azure-ai-documentintelligence>=1.0.0
```

---

## 5. Node.js Setup

```bash
cd pgx-bridge_v02/pgx-parser-ui

# Install dependencies
npm install

# Or use npm ci for production (faster, uses package-lock.json)
npm ci

# Build for production (optional, for static hosting)
npm run build
```

---

## 6. Project Configuration

### Backend Environment Variables

```bash
cd pgx-bridge_v02/pgx-parser-backend-py

# Copy example to create .env file
cp .env.example .env

# Edit .env file with your Azure credentials
nano .env  # or vim, vi, etc.
```

**Required Variables in `.env`:**
```bash
# Azure OpenAI (REQUIRED)
AZURE_OPENAI_API_KEY=your_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=gpt-4
AZURE_OPENAI_API_VERSION=2024-02-15-preview

# Azure Document Intelligence (OPTIONAL)
AZURE_DOC_INTELLIGENCE_ENDPOINT=https://your-resource.cognitiveservices.azure.com/
AZURE_DOC_INTELLIGENCE_KEY=your_key_here

# CORS Settings
ALLOWED_ORIGINS=http://localhost:3000,http://your-server-ip:3000
```

### Frontend Environment Variables

```bash
cd pgx-bridge_v02/pgx-parser-ui

# Copy example
cp .env.example .env

# Edit if needed (usually not required for development)
nano .env
```

**Frontend `.env` (optional):**
```bash
# Only needed if backend is on different server
REACT_APP_API_BASE=http://your-backend-server:8000
```

### Create Output Directory

```bash
cd pgx-bridge_v02
mkdir -p out
chmod 755 out
```

---

## 7. Starting the Application

### Start Backend (Development Mode)

```bash
cd pgx-bridge_v02/pgx-parser-backend-py

# Activate virtual environment
source venv/bin/activate

# Start server
uvicorn main:app --host 10.241.1.171 --port 8010 --reload

# Or use the startup script
cd ..
chmod +x start-backend.sh
./start-backend.sh
```

### Start Frontend (Development Mode)

```bash
cd pgx-bridge_v02/pgx-parser-ui

# Start React dev server
npm start

# Or use the startup script
cd ..
chmod +x start-frontend.sh
./start-frontend.sh
```

### Access the Application

- **Frontend**: http://server-ip:3000
- **Backend API**: http://server-ip:8000
- **API Docs**: http://server-ip:8000/docs

### Firewall Configuration

If your server has a firewall:

```bash
# Ubuntu/Debian (ufw)
sudo ufw allow 3000/tcp
sudo ufw allow 8000/tcp

# CentOS/RHEL (firewalld)
sudo firewall-cmd --permanent --add-port=3000/tcp
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

---

## 8. Running as a Service

### Backend Systemd Service

Create `/etc/systemd/system/pgx-backend.service`:

```ini
[Unit]
Description=PGX Parser Backend
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/pgx-bridge_v02/pgx-parser-backend-py
Environment="PATH=/path/to/pgx-bridge_v02/pgx-parser-backend-py/venv/bin"
ExecStart=/path/to/pgx-bridge_v02/pgx-parser-backend-py/venv/bin/uvicorn main:app --host 10.241.1.171 --port 8010
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Frontend Systemd Service (Production Build)

Create `/etc/systemd/system/pgx-frontend.service`:

```ini
[Unit]
Description=PGX Parser Frontend
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/pgx-bridge_v02/pgx-parser-ui
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services (start on boot)
sudo systemctl enable pgx-backend
sudo systemctl enable pgx-frontend

# Start services
sudo systemctl start pgx-backend
sudo systemctl start pgx-frontend

# Check status
sudo systemctl status pgx-backend
sudo systemctl status pgx-frontend

# View logs
sudo journalctl -u pgx-backend -f
sudo journalctl -u pgx-frontend -f
```

---

## 9. Nginx Reverse Proxy (Optional)

### Why Use Nginx?

- Serve both frontend and backend on port 80/443
- Add SSL/TLS encryption
- Better performance for static files
- Load balancing (if needed)

### Nginx Configuration

Create `/etc/nginx/sites-available/pgx-parser`:

```nginx
server {
    listen 80;
    server_name your-domain.com;  # or server IP

    # Frontend
    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }

    # Backend API
    location /api/ {
        proxy_pass http://10.241.1.171:8010/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Increase timeouts for large file uploads
        proxy_connect_timeout 300s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;
    }

    # API docs
    location /docs {
        proxy_pass http://10.241.1.171:8010/docs;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
    }

    # Increase max upload size for PDF files
    client_max_body_size 100M;
}
```

### Enable Nginx Configuration

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/pgx-parser /etc/nginx/sites-enabled/

# Test configuration
sudo nginx -t

# Restart Nginx
sudo systemctl restart nginx

# Enable Nginx on boot
sudo systemctl enable nginx
```

### SSL/TLS with Let's Encrypt (Optional)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx  # Ubuntu
sudo dnf install -y certbot python3-certbot-nginx  # CentOS

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal is configured automatically
```

---

## 10. Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| Port already in use | Check: `sudo lsof -i :8000`, kill process or change port |
| Permission denied | Check file permissions, use `chmod +x` for scripts |
| Module not found | Activate virtual environment, reinstall requirements |
| Azure API error | Verify `.env` file has correct credentials |
| CPIC table not found | Ensure `annotations/` folder transferred correctly |
| Cannot access from browser | Check firewall rules, verify services running |

### Check Service Status

```bash
# Backend health check
curl http://10.241.1.171:8010/healthz

# Check logs
tail -f pgx-parser-backend-py/logs/*.log
sudo journalctl -u pgx-backend -f
```

### Verify Python Environment

```bash
source pgx-parser-backend-py/venv/bin/activate
python -c "
import fastapi
import uvicorn
import openai
import docx
print('All packages imported successfully')
"
```

### Test CPIC Annotation

```bash
cd pgx-parser-backend-py
source venv/bin/activate
python test_cpic_integration.py
```

### Port Forwarding (for Remote Access)

If accessing from your local machine:

```bash
# SSH tunnel from local machine
ssh -L 8000:10.241.1.171:8010 -L 3000:localhost:3000 user@server
```

Then access:
- Frontend: http://localhost:3000
- Backend: http://10.241.1.171:8010

---

## Quick Reference Commands

```bash
# Start backend (development)
cd pgx-parser-backend-py && source venv/bin/activate && uvicorn main:app --host 10.241.1.171 --port 8010

# Start frontend (development)
cd pgx-parser-ui && npm start

# Start services (production)
sudo systemctl start pgx-backend
sudo systemctl start pgx-frontend

# View logs
sudo journalctl -u pgx-backend -f
sudo journalctl -u pgx-frontend -f

# Restart services
sudo systemctl restart pgx-backend
sudo systemctl restart pgx-frontend

# Stop services
sudo systemctl stop pgx-backend
sudo systemctl stop pgx-frontend
```

---

## Production Deployment Checklist

- [ ] Transfer all required files (exclude patient data, node_modules, __pycache__)
- [ ] Install system packages (Python 3.11, Node.js 18+)
- [ ] Create Python virtual environment
- [ ] Install Python dependencies (`pip install -r requirements.txt`)
- [ ] Install Node.js dependencies (`npm ci`)
- [ ] Create `.env` files with Azure credentials
- [ ] Create `out/` directory with proper permissions
- [ ] Test backend: `curl http://10.241.1.171:8010/healthz`
- [ ] Test frontend: Access http://server-ip:3000
- [ ] Configure firewall rules (ports 3000, 8000)
- [ ] Set up systemd services (optional)
- [ ] Configure Nginx reverse proxy (optional)
- [ ] Set up SSL/TLS certificates (optional)
- [ ] Configure log rotation
- [ ] Set up monitoring/alerting
- [ ] Document server credentials and configuration

---

## Security Considerations

1. **Never commit `.env` files** - Store credentials securely
2. **Use SSL/TLS in production** - Encrypt data in transit
3. **Restrict access** - Use firewall rules, VPN, or IP whitelisting
4. **Keep packages updated** - Regularly update dependencies
5. **Monitor logs** - Watch for suspicious activity
6. **Backup configuration** - Document all settings
7. **Use environment-specific configs** - Separate dev/staging/production

---

*For additional help, refer to DEVELOPER_GUIDE.md and TROUBLESHOOTING.md*
