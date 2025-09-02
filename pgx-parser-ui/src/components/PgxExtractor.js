import React, { useState } from 'react';
import { extractPgxData } from '../api';

function PgxExtractor() {
  // State management
  const [keyword, setKeyword] = useState('Patient Genotype');
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
      const response = await extractPgxData(keyword, file);
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

  // Render patient information table
  const renderPatientTable = () => {
    if (!result || !result.document_intelligence || !result.document_intelligence.patient_info) {
      return null;
    }

    const patientData = result.document_intelligence.patient_info;
    const hasData = Object.values(patientData).some(value => value && value !== 'Not found');
    
    if (!hasData) {
      return (
        <div className="patient-info-container">
          <h4>Patient Information</h4>
          <p>No patient information found on the first page.</p>
        </div>
      );
    }

    // Table 1 fields
    const table1Fields = [
      { key: 'patient_name', label: 'Patient Name' },
      { key: 'date_of_birth', label: 'Date of Birth' },
      { key: 'test', label: 'Test' },
      { key: 'report_date', label: 'Report Date' },
      { key: 'report_id', label: 'Report ID' }
    ];

    // Table 2 fields
    const table2Fields = [
      { key: 'cohort', label: 'Cohort' },
      { key: 'sample_type', label: 'Sample Type' },
      { key: 'sample_collection_date', label: 'Sample Collection Date' },
      { key: 'sample_received_date', label: 'Sample Received Date' },
      { key: 'processed_date', label: 'Processed Date' },
      { key: 'ordering_clinician', label: 'Ordering Clinician' },
      { key: 'npi', label: 'NPI' },
      { key: 'indication_for_testing', label: 'Indication for Testing' }
    ];

    return (
      <div className="patient-info-container">
        <h4>Patient Information</h4>
        
        {/* Patient Demographics Table */}
        <div className="patient-table-section">
          <h5>Patient Demographics</h5>
          <table className="patient-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {table1Fields.map(field => (
                <tr key={field.key} className={!patientData[field.key] ? 'not-found' : ''}>
                  <td className="field-name">{field.label}</td>
                  <td className="field-value">{patientData[field.key] || 'Not found'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Sample Information Table */}
        <div className="patient-table-section">
          <h5>Sample Information</h5>
          <table className="patient-table">
            <thead>
              <tr>
                <th>Field</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {table2Fields.map(field => (
                <tr key={field.key} className={!patientData[field.key] ? 'not-found' : ''}>
                  <td className="field-name">{field.label}</td>
                  <td className="field-value">{patientData[field.key] || 'Not found'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    );
  };

  // Render gene table
  const renderGeneTable = () => {
    if (!result || !result.document_intelligence || !result.document_intelligence.pgx_genes || result.document_intelligence.pgx_genes.length === 0) {
      return <p>No PGX gene data found in the document.</p>;
    }

    return (
      <div className="gene-table-container">
        <h4>PGX Gene Data</h4>
        <table className="gene-table">
          <thead>
            <tr>
              <th>Gene</th>
              <th>Genotype</th>
              <th>Metabolizer Status</th>
            </tr>
          </thead>
          <tbody>
            {result.document_intelligence.pgx_genes.map((gene, index) => (
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
            disabled={loading}
          />
        </div>

        <button type="submit" disabled={loading || !keyword || !file}>
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
              <strong>Keyword used:</strong> "{result.meta.keyword}"<br/>
              <strong>Pages analyzed:</strong> {result.meta.matched_pages.join(', ')} ({result.meta.matched_pages_count} page{result.meta.matched_pages_count !== 1 ? 's' : ''})<br/>
              <strong>Extraction method:</strong> {result.extraction_method}
            </div>
          )}

          {/* Patient Information */}
          {renderPatientTable()}

          {/* Gene table */}
          {renderGeneTable()}

          {/* LLM Comparison Results */}
          {result.comparison_available && result.llm_extraction && (
            <div className="llm-comparison">
              <h4>LLM Extraction Results (Comparison)</h4>
              <p><strong>Method:</strong> {result.llm_extraction.extraction_method}</p>
              
              {/* LLM Patient Info */}
              <div className="llm-patient-section">
                <h5>LLM Patient Information</h5>
                <table className="patient-table">
                  <thead>
                    <tr>
                      <th>Field</th>
                      <th>LLM Result</th>
                      <th>Document Intelligence</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.keys(result.llm_extraction.patient_info).map(key => (
                      <tr key={key}>
                        <td className="field-name">{key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase())}</td>
                        <td className="field-value">{result.llm_extraction.patient_info[key] || 'Not found'}</td>
                        <td className="field-value">{result.document_intelligence.patient_info[key] || 'Not found'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              {/* LLM PGX Genes */}
              <div className="llm-genes-section">
                <h5>LLM PGX Gene Results</h5>
                <table className="gene-table">
                  <thead>
                    <tr>
                      <th>Gene</th>
                      <th>LLM Genotype</th>
                      <th>LLM Status</th>
                      <th>DI Genotype</th>
                      <th>DI Status</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.llm_extraction.pgx_genes.map((llmGene, index) => {
                      const diGene = result.document_intelligence.pgx_genes.find(g => g.gene === llmGene.gene);
                      return (
                        <tr key={index}>
                          <td className="gene-name">{llmGene.gene}</td>
                          <td className="genotype">{llmGene.genotype}</td>
                          <td className="metabolizer-status">{llmGene.metabolizer_status}</td>
                          <td className="genotype">{diGene?.genotype || 'Not found'}</td>
                          <td className="metabolizer-status">{diGene?.metabolizer_status || 'Not found'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {/* Download as CSV button */}
          {result.document_intelligence && result.document_intelligence.pgx_genes && result.document_intelligence.pgx_genes.length > 0 && (
            <button 
              className="download-csv"
              onClick={() => downloadAsCSV(result.document_intelligence.pgx_genes, result.document_intelligence.patient_info, result.meta.original_filename)}
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
function downloadAsCSV(genes, patientInfo, filename) {
  const csvContent = [
    ['Gene', 'Genotype', 'Metabolizer Status'],
    ...genes.map(g => [g.gene, g.genotype, g.metabolizer_status])
  ].map(row => row.join(',')).join('\n');

  const patientInfoContent = Object.keys(patientInfo).map(key => `${key}: ${patientInfo[key]}`).join('\n');

  const blob = new Blob([patientInfoContent + '\n\n' + csvContent], { type: 'text/csv' });
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `pgx_genes_${filename.replace('.pdf', '')}.csv`;
  a.click();
  window.URL.revokeObjectURL(url);
}

export default PgxExtractor;