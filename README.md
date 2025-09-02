# PGX Parser - PDF Processing with Azure Document Intelligence

A web application that filters PDF pages by keyword and analyzes them using Azure AI Document Intelligence's layout model.

## Prerequisites

- Python 3.11+
- Node.js 18+
- Azure AI Document Intelligence resource with API key

## Quick Start

### Backend Setup

```bash
cd pgx-parser-backend-py
cp .env.example .env
# Edit .env with your Azure credentials
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

### Frontend Setup

```bash
cd pgx-parser-ui
cp .env.example .env  # optional if using proxy
npm install
npm start
```

Open `http://localhost:3000` in your browser.

## Features

- Upload PDF files and search for keywords
- Case-insensitive keyword matching
- Filters PDF to only pages containing the keyword
- Sends filtered PDF to Azure Document Intelligence for layout analysis
- Returns enriched JSON with metadata and full Azure analysis results
- Skips Azure processing if no pages match (cost optimization)

## Architecture

- **Backend**: FastAPI (Python) with pypdf for PDF manipulation
- **Frontend**: React with minimal styling
- **AI Service**: Azure AI Document Intelligence (prebuilt-layout model)

## API Documentation

When the backend is running, visit `http://localhost:8000/docs` for interactive API documentation.

## License

MIT