import React, { useState } from 'react';
import { processDocument } from '../api';

function PgxProcessor() {
  // State management
  const [keyword, setKeyword] = useState('');
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // Handle form submission
  const handleSubmit = async (e) => {
    e.preventDefault();
    
    // Clear previous results
    setError(null);
    setResult(null);

    // Validate inputs
    if (!keyword.trim()) {
      setError('Please enter a keyword');
      return;
    }

    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    // Process document
    setLoading(true);
    try {
      const response = await processDocument(keyword, file);
      setResult(response);
    } catch (err) {
      setError(err.message || 'An error occurred while processing the document');
    } finally {
      setLoading(false);
    }
  };

  // Handle file selection
  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    if (selectedFile && selectedFile.type === 'application/pdf') {
      setFile(selectedFile);
      setError(null);
    } else if (selectedFile) {
      setError('Please select a PDF file');
      setFile(null);
    }
  };

  // Render matched pages summary
  const renderSummary = () => {
    if (!result || !result.meta) return null;

    const { matched_pages, matched_pages_count } = result.meta;

    if (matched_pages_count === 0) {
      return <div className="summary">{result.message}</div>;
    }

    return (
      <div className="summary">
        <strong>{matched_pages_count} page{matched_pages_count !== 1 ? 's' : ''} matched:</strong> {matched_pages.join(', ')}
      </div>
    );
  };

  return (
    <div className="pgx-processor">
      <form onSubmit={handleSubmit} className="processor-form">
        <div className="form-group">
          <label htmlFor="keyword">Keyword</label>
          <input
            type="text"
            id="keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="Enter keyword to search for"
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="file">PDF File</label>
          <input
            type="file"
            id="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading || !keyword || !file}>
          {loading ? 'Processing...' : 'Process PDF'}
        </button>
      </form>

      {/* Error display */}
      {error && (
        <div className="error-banner">
          <strong>Error:</strong> {error}
        </div>
      )}

      {/* Loading spinner */}
      {loading && (
        <div className="loading">
          <div className="spinner"></div>
          <p>Processing your PDF...</p>
        </div>
      )}

      {/* Results display */}
      {result && !loading && (
        <div className="results">
          <h2>Results</h2>
          {renderSummary()}
          <div className="json-output">
            <h3>Full Response</h3>
            <pre>{JSON.stringify(result, null, 2)}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

export default PgxProcessor;