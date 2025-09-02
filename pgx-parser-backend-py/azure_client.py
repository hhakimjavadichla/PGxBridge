"""
Azure AI Document Intelligence client wrapper.
"""

import os
import io
from typing import Dict, Any
from azure.core.credentials import AzureKeyCredential
from azure.ai.documentintelligence import DocumentIntelligenceClient
from azure.core.exceptions import AzureError


def create_client() -> DocumentIntelligenceClient:
    """
    Create and return an Azure Document Intelligence client using environment variables.
    
    Returns:
        Configured DocumentIntelligenceClient instance
        
    Raises:
        ValueError: If required environment variables are missing
    """
    endpoint = os.environ.get("AZURE_DI_ENDPOINT")
    api_key = os.environ.get("AZURE_DI_KEY")
    
    if not endpoint or not api_key:
        raise ValueError("Missing required environment variables: AZURE_DI_ENDPOINT and AZURE_DI_KEY")
    
    return DocumentIntelligenceClient(
        endpoint=endpoint,
        credential=AzureKeyCredential(api_key)
    )


def analyze_layout(pdf_bytes: bytes) -> Dict[str, Any]:
    """
    Analyze PDF layout using Azure Document Intelligence prebuilt-layout model.
    
    Args:
        pdf_bytes: PDF content as bytes
        
    Returns:
        AnalyzeResult as dictionary
        
    Raises:
        AzureError: If Azure service call fails
    """
    client = create_client()
    
    try:
        # Start analysis with prebuilt-layout model
        poller = client.begin_analyze_document(
            "prebuilt-layout",
            body=io.BytesIO(pdf_bytes)
        )
        
        # Wait for completion and get result
        result = poller.result()
        
        # Convert to dictionary for JSON serialization
        return result.as_dict()
        
    except AzureError as e:
        # Re-raise with more context
        raise AzureError(f"Azure Document Intelligence API error: {str(e)}") from e