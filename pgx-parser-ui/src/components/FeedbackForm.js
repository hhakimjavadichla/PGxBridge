import React, { useState } from 'react';
import '../styles/FeedbackForm.css';

const FEEDBACK_CATEGORIES = [
  { value: 'parsing_error', label: 'Parsing Error', description: 'Genotype was incorrectly extracted from PDF' },
  { value: 'annotation_error', label: 'Annotation Error', description: 'CPIC annotation is incorrect or missing' },
  { value: 'export_error', label: 'Export Error', description: 'Issues with Word/CSV export' },
  { value: 'other', label: 'Other', description: 'Other issues' }
];

function FeedbackForm({ isOpen, onClose, geneData, filename }) {
  const [category, setCategory] = useState('');
  const [description, setDescription] = useState('');
  const [genotypeExpected, setGenotypeExpected] = useState('');
  const [phenotypeExpected, setPhenotypeExpected] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState(null);
  const [feedbackId, setFeedbackId] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    setError(null);

    const formData = new FormData();
    formData.append('category', category);
    formData.append('description', description);
    
    if (geneData) {
      formData.append('gene', geneData.gene || '');
      formData.append('genotype_reported', geneData.genotype || '');
      formData.append('phenotype_reported', geneData.metabolizer_status || geneData.cpic_phenotype || '');
    }
    
    if (genotypeExpected) {
      formData.append('genotype_expected', genotypeExpected);
    }
    if (phenotypeExpected) {
      formData.append('phenotype_expected', phenotypeExpected);
    }
    if (filename) {
      formData.append('filename', filename);
    }

    try {
      const response = await fetch('/api/feedback/submit', {
        method: 'POST',
        body: formData
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error?.message || 'Failed to submit feedback');
      }

      const result = await response.json();
      setFeedbackId(result.feedback_id);
      setSubmitted(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setSubmitting(false);
    }
  };

  const handleClose = () => {
    setCategory('');
    setDescription('');
    setGenotypeExpected('');
    setPhenotypeExpected('');
    setSubmitted(false);
    setError(null);
    setFeedbackId(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="feedback-modal-overlay" onClick={handleClose}>
      <div className="feedback-modal" onClick={(e) => e.stopPropagation()}>
        <div className="feedback-modal-header">
          <h2>Report an Issue</h2>
          <button className="feedback-close-btn" onClick={handleClose}>&times;</button>
        </div>

        {submitted ? (
          <div className="feedback-success">
            <div className="success-icon">&#10003;</div>
            <h3>Feedback Submitted</h3>
            <p>Thank you for your feedback. Your reference ID is:</p>
            <code className="feedback-id">{feedbackId}</code>
            <p className="feedback-note">
              Our team will review your submission and use it to improve the annotation system.
            </p>
            <button className="feedback-btn primary" onClick={handleClose}>
              Close
            </button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="feedback-form">
            {geneData && (
              <div className="feedback-context">
                <h4>Issue Context</h4>
                <div className="context-grid">
                  <div className="context-item">
                    <span className="context-label">Gene:</span>
                    <span className="context-value">{geneData.gene}</span>
                  </div>
                  <div className="context-item">
                    <span className="context-label">Reported Genotype:</span>
                    <span className="context-value">{geneData.genotype}</span>
                  </div>
                  <div className="context-item">
                    <span className="context-label">Reported Phenotype:</span>
                    <span className="context-value">{geneData.metabolizer_status || 'N/A'}</span>
                  </div>
                  <div className="context-item">
                    <span className="context-label">CPIC Phenotype:</span>
                    <span className="context-value">{geneData.cpic_phenotype || 'Not found'}</span>
                  </div>
                  <div className="context-item">
                    <span className="context-label">Match Status:</span>
                    <span className={`context-value status-${geneData.cpic_match_status}`}>
                      {geneData.cpic_match_status || 'Unknown'}
                    </span>
                  </div>
                </div>
              </div>
            )}

            <div className="form-group">
              <label htmlFor="category">Issue Type *</label>
              <select
                id="category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                required
              >
                <option value="">Select issue type...</option>
                {FEEDBACK_CATEGORIES.map((cat) => (
                  <option key={cat.value} value={cat.value}>
                    {cat.label} - {cat.description}
                  </option>
                ))}
              </select>
            </div>

            <div className="form-group">
              <label htmlFor="description">Description *</label>
              <textarea
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Describe the issue in detail..."
                rows={4}
                required
              />
            </div>

            {(category === 'parsing_error' || category === 'annotation_error') && (
              <>
                <div className="form-group">
                  <label htmlFor="genotypeExpected">Expected Genotype (if different)</label>
                  <input
                    type="text"
                    id="genotypeExpected"
                    value={genotypeExpected}
                    onChange={(e) => setGenotypeExpected(e.target.value)}
                    placeholder="e.g., *1/*2"
                  />
                </div>

                <div className="form-group">
                  <label htmlFor="phenotypeExpected">Expected Phenotype (if different)</label>
                  <input
                    type="text"
                    id="phenotypeExpected"
                    value={phenotypeExpected}
                    onChange={(e) => setPhenotypeExpected(e.target.value)}
                    placeholder="e.g., Intermediate Metabolizer"
                  />
                </div>
              </>
            )}

            {error && (
              <div className="feedback-error">
                <strong>Error:</strong> {error}
              </div>
            )}

            <div className="feedback-actions">
              <button type="button" className="feedback-btn secondary" onClick={handleClose}>
                Cancel
              </button>
              <button type="submit" className="feedback-btn primary" disabled={submitting}>
                {submitting ? 'Submitting...' : 'Submit Feedback'}
              </button>
            </div>
          </form>
        )}
      </div>
    </div>
  );
}

export default FeedbackForm;
