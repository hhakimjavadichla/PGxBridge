# PGX Parser UI

React frontend for PDF keyword filtering and Azure Document Intelligence analysis.

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. (Optional) Configure environment:
   ```bash
   cp .env.example .env
   ```
   
   The app uses a proxy configuration in `package.json` by default, so this step is optional unless you need a different API base URL.

## Running the App

```bash
npm start
```

The app will open at `http://localhost:3000`

## Features

- Upload PDF files
- Enter keywords to search for (case-insensitive)
- View matched pages and full Azure Document Intelligence analysis
- Pretty-printed JSON output
- Loading states and error handling

## Usage

1. Enter a keyword in the text field
2. Select a PDF file using the file input
3. Click "Process PDF"
4. View results:
   - Summary of matched pages
   - Full JSON response with Azure analysis

## API Configuration

By default, the app proxies API requests to `http://localhost:8000` (configured in `package.json`).

To use a different API endpoint, set `REACT_APP_API_BASE` in your `.env` file.

## Build for Production

```bash
npm run build
```

This creates an optimized production build in the `build/` directory.