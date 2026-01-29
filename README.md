# PGX Parser - Pharmacogenomics Report Processing Application

A web application that extracts pharmacogenomics (PGx) data from PDF reports, validates against CPIC standards, and generates formatted Word documents for patient and EHR use.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Azure OpenAI resource with GPT-4 deployment
- (Optional) Azure AI Document Intelligence resource

## Quick Start

### Conda Environment
```bash
# Tested environment: pgxbridge_env
conda activate pgxbridge_env
```

### Backend Setup

```bash
cd pgx-parser-backend-py
cp .env.example .env
# Edit .env with your Azure credentials
pip install -r requirements.txt
uvicorn main:app --reload --host 10.241.1.171 --port 8010
```

### Frontend Setup

```bash
cd pgx-parser-ui
npm install
npm start
```

Open `http://localhost:3000` in your browser.

## Features

- **PGX Gene Extractor**: Upload PDF and extract patient info + gene data using Azure OpenAI
- **CPIC Validation**: Automatic phenotype validation against CPIC database (27K+ entries)
- **Word Report Generation**: Generate patient-facing and EHR-facing reports using Jinja2 templates (docxtpl)
- **CSV Export**: Export extracted data as CSV files
- **Folder Batch Processor**: Process multiple PDF files from a folder

## Architecture

- **Backend**: FastAPI (Python) with Azure OpenAI for LLM extraction
- **Frontend**: React.js with modern UI components
- **Templating**: docxtpl (Jinja2-based) for Word document generation
- **AI Service**: Azure OpenAI (GPT-4) for data extraction

## Key Endpoints

| Endpoint | Purpose |
|----------|----------|
| `POST /api/extract-pgx-data` | Extract patient info and gene data from PDF |
| `POST /api/generate-patient-report` | Generate patient-facing Word document |
| `POST /api/generate-ehr-report` | Generate EHR-facing Word document |
| `GET /healthz` | Health check |

## API Documentation

When the backend is running, visit `http://10.241.1.171:8010/docs` for interactive API documentation.

## License

MIT