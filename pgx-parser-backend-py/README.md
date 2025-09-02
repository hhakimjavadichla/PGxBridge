# PGX Parser Backend

FastAPI backend for PDF keyword filtering and Azure Document Intelligence analysis.

## Setup

1. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   ```bash
   cp .env.example .env
   ```
   
   Edit `.env` and add your Azure credentials:
   - `AZURE_DI_ENDPOINT`: Your Azure Document Intelligence endpoint
   - `AZURE_DI_KEY`: Your API key
   - `ALLOWED_ORIGINS`: Comma-separated list of allowed CORS origins

## Running the Server

```bash
uvicorn main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger documentation.

## Endpoints

### Health Check
- `GET /healthz` - Returns `{"ok": true}`

### Process Document
- `POST /api/process-document`
  - Content-Type: `multipart/form-data`
  - Fields:
    - `keyword` (string, required): Keyword to search for
    - `file` (file, required): PDF file to process
  - Returns: JSON with metadata and Azure analysis results

## Example Usage

```bash
curl -X POST http://localhost:8000/api/process-document \
  -F "keyword=revenue" \
  -F "file=@document.pdf"
```

## Azure Document Intelligence Limits

### File Size Limits
- **S0 tier**: 500 MB maximum file size
- **F0 (free) tier**: 4 MB maximum file size

### Page Processing Limits
- **F0 (free) tier**: Only the first 2 pages are processed
- **S0 tier**: All pages are processed

This backend enforces a 520 MB limit to provide headroom under Azure's limits.

For more information, see [Azure Document Intelligence layout model documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/prebuilt/layout?view=doc-intel-4.0.0).

## Error Handling

All errors return JSON in the format:
```json
{
  "error": {
    "type": "error_type",
    "message": "Human-readable error message"
  }
}
```

Common error types:
- `invalid_file_type`: Non-PDF file uploaded
- `file_too_large`: File exceeds size limit
- `azure_api_error`: Azure service error
- `pdf_search_error`: Error searching PDF content

## Development Notes

- PDFs are processed entirely in memory (no disk persistence)
- Case-insensitive keyword matching
- If no pages match the keyword, Azure is not called (cost optimization)
- Page numbers in responses are 1-indexed