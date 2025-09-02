import React, { useState } from 'react';
import { extractPgxData } from '../api';

function PgxExtractor() {
  // State management
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

    if (!file) {
      setError('Please select a PDF file');
      return;
    }

    // Process document
    setLoading(true);
    try {
      const response = await extractPgxData(file);
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

  // Render gene table
  const renderGeneTable = () => {
    if (!result || !result.pgx_genes || result.pgx_genes.length === 0) {
      return <p>No PGX gene data found in the document.</p>;
    }

    return (
      <div className="gene-table-container">
        <table className="gene-table">
          <thead>
            <tr>
              <th>Gene</th>
              <th>Genotype</th>
              <th>Metabolizer Status</th>
            </tr>
          </thead>
          <tbody>
            {result.pgx_genes.map((gene, index) => (
              <tr key={index} className={gene.genotype === 'Not found' ? 'not-found' : ''}>
                <td className="gene-name">{gene.gene}</td>
                <td className="genotype">{gene.genotype}</td>
                <td className="metabolizer-status">{gene.metabolizer_status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div className="pgx-extractor">
      <h2>PGX Gene Data Extractor</h2>
      <p className="description">
        Upload a PGX report PDF to extract genotype and metabolizer status for all 13 standard PGX genes.
      </p>

      <form onSubmit={handleSubmit} className="extractor-form">
        <div className="form-group">
          <label htmlFor="pgx-file">PGX Report PDF</label>
          <input
            type="file"
            id="pgx-file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading || !file}>
          {loading ? 'Extracting...' : 'Extract PGX Data'}
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
          <p>Extracting PGX gene data...</p>
        </div>
      )}

      {/* Results display */}
      {result && !loading && (
        <div className="results">
          <h3>Extracted PGX Gene Data</h3>
          
          {/* Summary */}
          {result.meta && (
            <div className="summary">
              <strong>Report:</strong> {result.meta.original_filename}<br/>
              <strong>Pages analyzed:</strong> {result.meta.matched_pages.join(', ')}<br/>
              <strong>Extraction method:</strong> {result.extraction_method}
            </div>
          )}

          {/* Gene table */}
          {renderGeneTable()}

          {/* Download as CSV button */}
          {result.pgx_genes && result.pgx_genes.length > 0 && (
            <button 
              className="download-csv"
              onClick={() => downloadAsCSV(result.pgx_genes, result.meta.original_filename)}
            >
              Download as CSV
            </button>
          )}
        </div>
      )}
    </div>
  );
}

// Helper function to download data as CSV
function downloadAsCSV(genes, filename) {
  const csvContent = [
    ['Gene', 'Genotype', 'Metabolizer Status'],
    ...genes.map(g => [g.gene, g.genotype, g.metabolizer_status])
  ].map(row => row.join(',')).join('\n');

  const blob = new Blob([csvContent], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `pgx_genes_${filename.replace('.pdf', '')}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}

export default PgxExtractor;