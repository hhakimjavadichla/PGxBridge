import React, { useState } from 'react';
import { extractPgxData } from '../api';

function PgxExtractor() {
  // State management
  const [keyword, setKeyword] = useState('Patient Genotype');
  const [file, setFile] = useState(null);
  const [files, setFiles] = useState([]);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [batchResults, setBatchResults] = useState([]);
  const [batchMode, setBatchMode] = useState(false);
  const [processingProgress, setProcessingProgress] = useState({ current: 0, total: 0 });
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

    if (!file && !files.length) {
      setError('Please select a PDF file or multiple files for batch processing');
      return;
    }

    // Process document
    setLoading(true);
    try {
      if (batchMode) {
        const responses = await Promise.all(files.map((file) => extractPgxData(keyword, file)));
        setBatchResults(responses);
      } else {
        const response = await extractPgxData(keyword, file);
        setResult(response);
      }
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

  const handleBatchFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const pdfFiles = selectedFiles.filter((file) => file.type === 'application/pdf');
    if (pdfFiles.length) {
      setFiles(pdfFiles);
      setError(null);
    } else {
      setError('Please select one or more PDF files');
      setFiles([]);
    }
  };

  // Helper function to get similarity class
  const getSimilarityClass = (score) => {
    if (score >= 0.9) {
      return 'high';
    } else if (score >= 0.7) {
      return 'medium';
    } else {
      return 'low';
    }
  };

  // Helper function to escape CSV values that contain commas, quotes, or newlines
  const escapeCSVValue = (value) => {
    if (value == null || value === '') return '';
    const stringValue = String(value);
    // If the value contains comma, quote, or newline, wrap it in quotes and escape internal quotes
    if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
      return `"${stringValue.replace(/"/g, '""')}"`;
    }
    return stringValue;
  };

  // Helper function to download patient data as CSV
  const downloadPatientCSV = (patientInfo, filename) => {
    const baseFilename = filename ? filename.replace('.pdf', '') : 'patient';
    
    // Define the exact 13 columns in order
    const columns = [
      'patient_name',
      'date_of_birth', 
      'test',
      'report_date',
      'report_id',
      'cohort',
      'sample_type',
      'sample_collection_date',
      'sample_received_date',
      'processed_date',
      'ordering_clinician',
      'npi',
      'indication_for_testing'
    ];
    
    // Create header row
    const headers = [
      'Patient Name',
      'Date Of Birth',
      'Test',
      'Report Date', 
      'Report Id',
      'Cohort',
      'Sample Type',
      'Sample Collection Date',
      'Sample Received Date',
      'Processed Date',
      'Ordering Clinician',
      'Npi',
      'Indication For Testing'
    ];
    
    // Create data row with proper CSV escaping
    const dataRow = columns.map(col => escapeCSVValue(patientInfo[col] || ''));
    
    const csvContent = [
      headers.join(','),
      dataRow.join(',')
    ].join('\n');
    
    // Download patient CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${baseFilename}_patient.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Helper function to download gene data as CSV
  const downloadGeneCSV = (genes, filename) => {
    const baseFilename = filename ? filename.replace('.pdf', '') : 'genes';
    
    const csvContent = [
      'Gene,Genotype,Metabolizer Status',
      ...genes.map(g => [
        escapeCSVValue(g.gene),
        escapeCSVValue(g.genotype),
        escapeCSVValue(g.metabolizer_status)
      ].join(','))
    ].join('\n');
    
    // Download gene CSV
    const blob = new Blob([csvContent], { type: 'text/csv' });
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${baseFilename}_genes.csv`;
    a.click();
    window.URL.revokeObjectURL(url);
  };

  // Updated function to download both CSV files
  function downloadSingleResultAsCSV(result, filename) {
    if (!result.llm_extraction) return;
    
    const patientInfo = result.llm_extraction.patient_info;
    const genes = result.llm_extraction.pgx_genes;
    
    // Download both files
    downloadPatientCSV(patientInfo, filename);
    setTimeout(() => downloadGeneCSV(genes, filename), 100); // Small delay to avoid browser blocking
  }

  return (
    <div className="pgx-extractor">
      <h2>PGX Gene Data Extractor</h2>
      <p className="description">
        Upload a PGX report PDF and enter a keyword that appears only in the pages containing the gene table.
        The system will extract genotype and metabolizer status for all 13 standard PGX genes.
      </p>

      <form onSubmit={handleSubmit} className="extractor-form">
        <div className="form-group">
          <label htmlFor="pgx-keyword">Keyword (appears only in PGX table pages)</label>
          <input
            type="text"
            id="pgx-keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="e.g., Patient Genotype"
            disabled={loading}
          />
          <small>Enter a unique keyword that only appears in the pages containing the PGX gene table</small>
        </div>

        <div className="form-group">
          <label htmlFor="pgx-file">PGX Report PDF</label>
          <input
            type="file"
            id="pgx-file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            disabled={loading || batchMode}
          />
          {batchMode && (
            <input
              type="file"
              id="pgx-files"
              accept=".pdf,application/pdf"
              multiple
              onChange={handleBatchFileChange}
              disabled={loading}
            />
          )}
        </div>

        <div className="form-group">
          <label>
            <input
              type="checkbox"
              checked={batchMode}
              onChange={(e) => setBatchMode(e.target.checked)}
            />
            Batch Processing
          </label>
        </div>

        <button type="submit" disabled={loading || !keyword || (!file && !files.length)}>
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
      {result && (
        <div className="results">
          <h3>AI-Parsed Results</h3>

          {/* LLM Results (Primary) */}
          {result.llm_extraction && (
            <div className="llm-primary-results">
              <h4>🤖 PGX Gene Analysis Results</h4>
              <p><strong>Method:</strong> {result.llm_extraction.extraction_method}</p>
                
              {/* LLM Patient Information */}
              <div className="patient-section">
                <h5>Patient Information</h5>
                <table className="patient-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(result.llm_extraction.patient_info).map(key => (
                      <tr key={key}>
                        <td className="field-name">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                        <td className="field-value">{result.llm_extraction.patient_info[key] || 'Not found'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* LLM Gene Results */}
              <div className="genes-section">
                <h5>PGX Gene Analysis</h5>
                <table className="gene-table">
                  <thead>
                    <tr>
                      <th>Gene</th>
                      <th>Genotype</th>
                      <th>Metabolizer Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.llm_extraction.pgx_genes.map((gene, index) => (
                      <tr key={index}>
                        <td className="gene-name">{gene.gene}</td>
                        <td className="genotype">{gene.genotype}</td>
                        <td className="metabolizer-status">{gene.metabolizer_status}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
                
              {/* Download CSV Button */}
              <div className="download-section">
                <button 
                  className="download-csv-btn"
                  onClick={() => downloadSingleResultAsCSV(result, file?.name)}
                  disabled={!result.llm_extraction}
                >
                  📊 Download CSV Files (Patient + Genes)
                </button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default PgxExtractor;