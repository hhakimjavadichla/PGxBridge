"""
Feedback Manager - Handle user feedback for PGX annotation issues.

This module provides functionality to collect, store, and manage user feedback
about parsing errors, annotation mismatches, and export issues.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class FeedbackCategory(str, Enum):
    """Categories of feedback issues."""
    PARSING_ERROR = "parsing_error"           # Genotype was incorrectly extracted from PDF
    ANNOTATION_ERROR = "annotation_error"     # CPIC annotation is incorrect or missing
    EXPORT_ERROR = "export_error"             # Issues with Word/CSV export
    OTHER = "other"                           # Other issues


class FeedbackStatus(str, Enum):
    """Status of feedback items."""
    PENDING = "pending"       # New feedback, not yet reviewed
    IN_REVIEW = "in_review"   # Being reviewed
    RESOLVED = "resolved"     # Issue has been addressed
    REJECTED = "rejected"     # Feedback was not valid


class FeedbackManager:
    """
    Manages user feedback for PGX annotation issues.
    
    Stores feedback in a JSON file for persistence and easy review.
    """
    
    _instance = None
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super(FeedbackManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize feedback manager."""
        if not hasattr(self, '_initialized'):
            self._initialized = True
            self._feedback_file = self._get_feedback_file_path()
            self._ensure_feedback_file()
    
    def _get_feedback_file_path(self) -> Path:
        """Get path to feedback storage file."""
        backend_dir = Path(__file__).parent
        project_root = backend_dir.parent
        feedback_dir = project_root / "feedback"
        feedback_dir.mkdir(exist_ok=True)
        return feedback_dir / "user_feedback.json"
    
    def _ensure_feedback_file(self):
        """Ensure feedback file exists with proper structure."""
        if not self._feedback_file.exists():
            initial_data = {
                "metadata": {
                    "created": datetime.now().isoformat(),
                    "version": "1.0",
                    "description": "User feedback for PGX annotation issues"
                },
                "feedback_items": []
            }
            self._save_feedback_data(initial_data)
            logger.info(f"Created feedback file: {self._feedback_file}")
    
    def _load_feedback_data(self) -> Dict:
        """Load feedback data from file."""
        try:
            with open(self._feedback_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading feedback data: {e}")
            return {"metadata": {}, "feedback_items": []}
    
    def _save_feedback_data(self, data: Dict):
        """Save feedback data to file."""
        try:
            with open(self._feedback_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving feedback data: {e}")
            raise
    
    def submit_feedback(
        self,
        category: str,
        description: str,
        gene: Optional[str] = None,
        genotype_reported: Optional[str] = None,
        genotype_expected: Optional[str] = None,
        phenotype_reported: Optional[str] = None,
        phenotype_expected: Optional[str] = None,
        patient_id: Optional[str] = None,
        filename: Optional[str] = None,
        additional_context: Optional[Dict] = None
    ) -> Dict:
        """
        Submit a new feedback item.
        
        Args:
            category: Type of issue (parsing_error, annotation_error, export_error, other)
            description: User's description of the issue
            gene: Gene name (if applicable)
            genotype_reported: Genotype extracted from PDF
            genotype_expected: What the genotype should be
            phenotype_reported: Phenotype from CPIC or PDF
            phenotype_expected: What the phenotype should be
            patient_id: Anonymized patient identifier
            filename: Name of the source PDF file
            additional_context: Any additional context data
            
        Returns:
            dict with feedback_id and confirmation
        """
        feedback_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().isoformat()
        
        feedback_item = {
            "feedback_id": feedback_id,
            "timestamp": timestamp,
            "category": category,
            "status": FeedbackStatus.PENDING.value,
            "description": description,
            "gene": gene,
            "genotype_reported": genotype_reported,
            "genotype_expected": genotype_expected,
            "phenotype_reported": phenotype_reported,
            "phenotype_expected": phenotype_expected,
            "patient_id": patient_id,
            "filename": filename,
            "additional_context": additional_context or {},
            "resolution_notes": None,
            "resolved_at": None
        }
        
        # Load, append, save
        data = self._load_feedback_data()
        data["feedback_items"].append(feedback_item)
        self._save_feedback_data(data)
        
        logger.info(f"Feedback submitted: {feedback_id} - {category} - {gene or 'N/A'}")
        
        return {
            "success": True,
            "feedback_id": feedback_id,
            "message": f"Feedback submitted successfully. Reference ID: {feedback_id}"
        }
    
    def get_all_feedback(
        self,
        category: Optional[str] = None,
        status: Optional[str] = None,
        gene: Optional[str] = None
    ) -> List[Dict]:
        """
        Get all feedback items, optionally filtered.
        
        Args:
            category: Filter by category
            status: Filter by status
            gene: Filter by gene name
            
        Returns:
            List of feedback items
        """
        data = self._load_feedback_data()
        items = data.get("feedback_items", [])
        
        # Apply filters
        if category:
            items = [i for i in items if i.get("category") == category]
        if status:
            items = [i for i in items if i.get("status") == status]
        if gene:
            items = [i for i in items if i.get("gene", "").upper() == gene.upper()]
        
        # Sort by timestamp descending (newest first)
        items.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        
        return items
    
    def get_feedback_by_id(self, feedback_id: str) -> Optional[Dict]:
        """Get a specific feedback item by ID."""
        data = self._load_feedback_data()
        for item in data.get("feedback_items", []):
            if item.get("feedback_id") == feedback_id:
                return item
        return None
    
    def update_feedback_status(
        self,
        feedback_id: str,
        new_status: str,
        resolution_notes: Optional[str] = None
    ) -> Dict:
        """
        Update the status of a feedback item.
        
        Args:
            feedback_id: ID of the feedback item
            new_status: New status value
            resolution_notes: Notes about the resolution
            
        Returns:
            dict with success status
        """
        data = self._load_feedback_data()
        
        for item in data.get("feedback_items", []):
            if item.get("feedback_id") == feedback_id:
                item["status"] = new_status
                if resolution_notes:
                    item["resolution_notes"] = resolution_notes
                if new_status == FeedbackStatus.RESOLVED.value:
                    item["resolved_at"] = datetime.now().isoformat()
                
                self._save_feedback_data(data)
                logger.info(f"Feedback {feedback_id} updated to status: {new_status}")
                
                return {"success": True, "message": f"Feedback {feedback_id} updated"}
        
        return {"success": False, "message": f"Feedback {feedback_id} not found"}
    
    def get_summary(self) -> Dict:
        """
        Get summary statistics of all feedback.
        
        Returns:
            dict with summary statistics
        """
        data = self._load_feedback_data()
        items = data.get("feedback_items", [])
        
        total = len(items)
        by_category = {}
        by_status = {}
        by_gene = {}
        
        for item in items:
            # Count by category
            cat = item.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1
            
            # Count by status
            status = item.get("status", "unknown")
            by_status[status] = by_status.get(status, 0) + 1
            
            # Count by gene
            gene = item.get("gene")
            if gene:
                by_gene[gene] = by_gene.get(gene, 0) + 1
        
        return {
            "total_feedback": total,
            "by_category": by_category,
            "by_status": by_status,
            "by_gene": by_gene,
            "pending_count": by_status.get("pending", 0)
        }
    
    def export_feedback_csv(self) -> str:
        """
        Export all feedback to CSV format.
        
        Returns:
            CSV string of all feedback
        """
        import csv
        from io import StringIO
        
        data = self._load_feedback_data()
        items = data.get("feedback_items", [])
        
        if not items:
            return "No feedback items to export"
        
        output = StringIO()
        fieldnames = [
            "feedback_id", "timestamp", "category", "status", "gene",
            "genotype_reported", "genotype_expected", 
            "phenotype_reported", "phenotype_expected",
            "description", "filename", "resolution_notes", "resolved_at"
        ]
        
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(items)
        
        return output.getvalue()


# Global instance
_feedback_manager = None


def get_feedback_manager() -> FeedbackManager:
    """Get or create global feedback manager instance."""
    global _feedback_manager
    if _feedback_manager is None:
        _feedback_manager = FeedbackManager()
    return _feedback_manager
