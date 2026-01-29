import React, { useState } from 'react';
import { extractPgxData } from '../api';
import '../styles/FolderBatchProcessor.css';

function FolderBatchProcessor() {
  const [keyword, setKeyword] = useState('Patient Genotype');
  const [files, setFiles] = useState([]);
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState({ current: 0, total: 0 });
  const [results, setResults] = useState([]);
  const [error, setError] = useState(null);
  const [generatingPatientReports, setGeneratingPatientReports] = useState(false);
  const [generatingEhrReports, setGeneratingEhrReports] = useState(false);

  // Handle folder/file selection
  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const pdfFiles = selectedFiles.filter(file => file.type === 'application/pdf');
    
    if (pdfFiles.length === 0) {
      setError('No PDF files found. Please select a folder containing PDF files.');
      setFiles([]);
      return;
    }
    
    setFiles(pdfFiles);
    setError(null);
    console.log(`Selected ${pdfFiles.length} PDF files`);
  };

  // Process all PDFs in the folder
  const handleProcessFolder = async () => {
    if (files.length === 0) {
      setError('Please select a folder containing PDF files');
      return;
    }

    if (!keyword.trim()) {
      setError('Please enter a keyword');
      return;
    }

    setProcessing(true);
    setError(null);
    setResults([]);
    setProgress({ current: 0, total: files.length });

    const processedResults = [];
    const errors = [];

    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      setProgress({ current: i + 1, total: files.length });

      try {
        console.log(`Processing ${i + 1}/${files.length}: ${file.name}`);
        const response = await extractPgxData(keyword, file);
        
        processedResults.push({
          filename: file.name,
          success: true,
          data: response
        });
      } catch (err) {
        console.error(`Error processing ${file.name}:`, err);
        errors.push({
          filename: file.name,
          error: err.message || 'Unknown error'
        });
        
        processedResults.push({
          filename: file.name,
          success: false,
          error: err.message || 'Unknown error'
        });
      }
    }

    setResults(processedResults);
    setProcessing(false);

    if (errors.length > 0) {
      setError(`Completed with ${errors.length} error(s). See results below.`);
    }
  };

  // Generate batch patient reports as ZIP
  const generateBatchPatientReports = async () => {
    const successfulResults = results.filter(r => r.success);
    if (successfulResults.length === 0) {
      setError('No successful results to generate reports from');
      return;
    }

    setGeneratingPatientReports(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('results_json', JSON.stringify(successfulResults));

      const response = await fetch('/api/generate-batch-patient-reports', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to generate reports');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `PGx_Patient_Reports_${new Date().toISOString().split('T')[0]}.zip`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to generate patient reports: ' + err.message);
    } finally {
      setGeneratingPatientReports(false);
    }
  };

  // Generate batch EHR reports as ZIP
  const generateBatchEhrReports = async () => {
    const successfulResults = results.filter(r => r.success);
    if (successfulResults.length === 0) {
      setError('No successful results to generate reports from');
      return;
    }

    setGeneratingEhrReports(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('results_json', JSON.stringify(successfulResults));

      const response = await fetch('/api/generate-batch-ehr-reports', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to generate reports');
      }

      const blob = await response.blob();
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.download = `PGx_EHR_Notes_${new Date().toISOString().split('T')[0]}.zip`;
      link.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      setError('Failed to generate EHR reports: ' + err.message);
    } finally {
      setGeneratingEhrReports(false);
    }
  };

  // Export consolidated results as CSV
  const exportConsolidatedCSV = () => {
    if (results.length === 0) return;

    const successfulResults = results.filter(r => r.success);
    if (successfulResults.length === 0) {
      setError('No successful results to export');
      return;
    }

    // Build consolidated table with patient info + all genes
    const csvRows = [];
    
    // Header row
    const headers = [
      'Filename',
      'Patient Name',
      'Date of Birth',
      'Report Date',
      'Report ID',
      'Gene',
      'Genotype',
      'PDF Interpretation',
      'CPIC Phenotype',
      'CPIC Phenotype (Full)',
      'CPIC Category',
      'CPIC Activity Score',
      'CPIC EHR Priority',
      'CPIC High Risk',
      'CPIC Match Status',
      'CPIC Validation Message'
    ];
    csvRows.push(headers.join(','));

    // Data rows - one row per gene per patient
    successfulResults.forEach(result => {
      const patientInfo = result.data.llm_extraction?.patient_info || {};
      const genes = result.data.llm_extraction?.pgx_genes || [];

      genes.forEach(gene => {
        const row = [
          escapeCSV(result.filename),
          escapeCSV(patientInfo.patient_name || ''),
          escapeCSV(patientInfo.date_of_birth || ''),
          escapeCSV(patientInfo.report_date || ''),
          escapeCSV(patientInfo.report_id || ''),
          escapeCSV(gene.gene),
          escapeCSV(gene.genotype),
          escapeCSV(gene.metabolizer_status),
          escapeCSV(gene.cpic_phenotype || ''),
          escapeCSV(gene.cpic_phenotype_full || ''),
          escapeCSV(gene.cpic_phenotype_category || ''),
          escapeCSV(gene.cpic_activity_score || ''),
          escapeCSV(gene.cpic_ehr_priority || ''),
          escapeCSV(gene.cpic_is_high_risk ? 'Yes' : 'No'),
          escapeCSV(gene.cpic_match_status || ''),
          escapeCSV(gene.cpic_validation_message || '')
        ];
        csvRows.push(row.join(','));
      });
    });

    // Download CSV
    const csvContent = csvRows.join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `pgx_batch_results_${new Date().toISOString().split('T')[0]}.csv`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // Helper function to escape CSV values
  const escapeCSV = (value) => {
    if (value == null || value === '') return '';
    const stringValue = String(value);
    if (stringValue.includes(',') || stringValue.includes('"') || stringValue.includes('\n')) {
      return `"${stringValue.replace(/"/g, '""')}"`;
    }
    return stringValue;
  };

  // Get summary statistics
  const getSummary = () => {
    if (results.length === 0) return null;

    const successful = results.filter(r => r.success).length;
    const failed = results.filter(r => !r.success).length;
    
    let totalGenes = 0;
    let highRiskCount = 0;
    let exactMatches = 0;
    
    results.forEach(result => {
      if (result.success && result.data.llm_extraction) {
        const genes = result.data.llm_extraction.pgx_genes || [];
        totalGenes += genes.length;
        highRiskCount += genes.filter(g => g.cpic_is_high_risk).length;
        exactMatches += genes.filter(g => g.cpic_match_status === 'exact_match').length;
      }
    });

    return {
      successful,
      failed,
      totalGenes,
      highRiskCount,
      exactMatches,
      matchRate: totalGenes > 0 ? ((exactMatches / totalGenes) * 100).toFixed(1) : 0
    };
  };

  const summary = getSummary();

  return (
    <div className="folder-batch-processor">
      <h2>📁 Folder Batch Processor</h2>
      <p className="description">
        Select a folder containing multiple PDF files to process them all at once and export a consolidated table.
      </p>

      {/* Input Section */}
      <div className="input-section">
        <div className="form-group">
          <label htmlFor="keyword">Keyword (appears in PGX table pages):</label>
          <input
            type="text"
            id="keyword"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
            placeholder="e.g., Patient Genotype"
            disabled={processing}
          />
        </div>

        <div className="form-group">
          <label htmlFor="folder">Select Folder:</label>
          <input
            type="file"
            id="folder"
            webkitdirectory=""
            directory=""
            multiple
            onChange={handleFileChange}
            disabled={processing}
            accept=".pdf"
          />
          {files.length > 0 && (
            <p className="file-count">✅ {files.length} PDF file(s) selected</p>
          )}
        </div>

        <button
          className="process-btn"
          onClick={handleProcessFolder}
          disabled={processing || files.length === 0}
        >
          {processing ? '⏳ Processing...' : '🚀 Process All PDFs'}
        </button>
      </div>

      {/* Progress Bar */}
      {processing && (
        <div className="progress-section">
          <div className="progress-bar">
            <div 
              className="progress-fill" 
              style={{ width: `${(progress.current / progress.total) * 100}%` }}
            />
          </div>
          <p className="progress-text">
            Processing {progress.current} of {progress.total} files...
          </p>
        </div>
      )}

      {/* Error Message */}
      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}

      {/* Summary Statistics */}
      {summary && (
        <div className="summary-section">
          <h3>📊 Processing Summary</h3>
          <div className="summary-grid">
            <div className="summary-item">
              <span className="summary-label">Total Files:</span>
              <span className="summary-value">{results.length}</span>
            </div>
            <div className="summary-item success">
              <span className="summary-label">Successful:</span>
              <span className="summary-value">{summary.successful}</span>
            </div>
            <div className="summary-item error">
              <span className="summary-label">Failed:</span>
              <span className="summary-value">{summary.failed}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Total Genes:</span>
              <span className="summary-value">{summary.totalGenes}</span>
            </div>
            <div className="summary-item high-risk">
              <span className="summary-label">High-Risk Variants:</span>
              <span className="summary-value">{summary.highRiskCount}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Exact Matches:</span>
              <span className="summary-value">{summary.exactMatches}</span>
            </div>
            <div className="summary-item">
              <span className="summary-label">Match Rate:</span>
              <span className="summary-value">{summary.matchRate}%</span>
            </div>
          </div>

          <div className="export-buttons">
            <button
              className="export-btn"
              onClick={exportConsolidatedCSV}
              disabled={summary.successful === 0}
            >
              📥 Export Consolidated CSV
            </button>
            <button
              className="export-btn patient-report-btn"
              onClick={generateBatchPatientReports}
              disabled={summary.successful === 0 || generatingPatientReports}
            >
              {generatingPatientReports ? '⏳ Generating...' : '📄 Generate Patient Reports (ZIP)'}
            </button>
            <button
              className="export-btn ehr-report-btn"
              onClick={generateBatchEhrReports}
              disabled={summary.successful === 0 || generatingEhrReports}
            >
              {generatingEhrReports ? '⏳ Generating...' : '🏥 Generate EHR Notes (ZIP)'}
            </button>
          </div>
        </div>
      )}

      {/* Results List */}
      {results.length > 0 && (
        <div className="results-section">
          <h3>📋 Processing Results</h3>
          <div className="results-list">
            {results.map((result, index) => (
              <div 
                key={index} 
                className={`result-item ${result.success ? 'success' : 'error'}`}
              >
                <div className="result-header">
                  <span className="result-icon">
                    {result.success ? '✅' : '❌'}
                  </span>
                  <span className="result-filename">{result.filename}</span>
                </div>
                
                {result.success ? (
                  <div className="result-details">
                    <div className="result-info">
                      <strong>Patient:</strong> {result.data.llm_extraction?.patient_info?.patient_name || 'N/A'}
                    </div>
                    <div className="result-info">
                      <strong>Report ID:</strong> {result.data.llm_extraction?.patient_info?.report_id || 'N/A'}
                    </div>
                    <div className="result-info">
                      <strong>Genes:</strong> {result.data.llm_extraction?.pgx_genes?.length || 0}
                    </div>
                    <div className="result-info">
                      <strong>High-Risk:</strong> {result.data.llm_extraction?.pgx_genes?.filter(g => g.cpic_is_high_risk).length || 0}
                    </div>
                  </div>
                ) : (
                  <div className="result-error">
                    <strong>Error:</strong> {result.error}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default FolderBatchProcessor;
