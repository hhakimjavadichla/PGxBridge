"""
LLM-based parsing utilities using Azure OpenAI for extracting patient and PGX data.
"""

import os
import json
import logging
from typing import Dict, List, Optional, Tuple
from openai import AzureOpenAI
from schemas import PatientInfo, PgxGeneData
from pgx_parser import PGX_GENES

logger = logging.getLogger(__name__)


class AzureLLMParser:
    """Azure OpenAI-based parser for medical documents."""
    
    def __init__(self):
        """Initialize Azure OpenAI client."""
        self.client = AzureOpenAI(
            api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
            api_version=os.environ.get("AZURE_OPENAI_API_VERSION", "2024-02-15-preview"),
            azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        self.deployment_name = os.environ.get("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")
        
        if not all([self.client.api_key, self.client._base_url]):
            raise ValueError("Missing required Azure OpenAI environment variables")
    
    def extract_patient_info_llm(self, content: str) -> PatientInfo:
        """
        Extract patient information using LLM from first page content.
        
        Args:
            content: Text content from the first page
            
        Returns:
            PatientInfo object with extracted data
        """
        try:
            prompt = self._create_patient_info_prompt(content)
            response = self._call_llm(prompt)
            return self._parse_patient_response(response)
        except Exception as e:
            logger.error(f"Error extracting patient info with LLM: {e}")
            return PatientInfo()
    
    def extract_pgx_data_llm(self, content: str) -> List[PgxGeneData]:
        """
        Extract PGX gene data using LLM from filtered page content.
        
        Args:
            content: Text content from PGX table pages
            
        Returns:
            List of PgxGeneData objects
        """
        try:
            prompt = self._create_pgx_prompt(content)
            response = self._call_llm(prompt)
            return self._parse_pgx_response(response)
        except Exception as e:
            logger.error(f"Error extracting PGX data with LLM: {e}")
            return [
                PgxGeneData(
                    gene=gene,
                    genotype="Not found",
                    metabolizer_status="Not found"
                )
                for gene in PGX_GENES
            ]
    
    def _create_patient_info_prompt(self, content: str) -> str:
        """Create prompt for patient information extraction."""
        return f"""
You are a medical document parser. Extract patient information from the following text content from the first page of a PGX report.

Extract the following fields and return them as a JSON object:
- patient_name: Patient's full name
- date_of_birth: Date of birth (any format)
- test: Test name or type
- report_date: Report date
- report_id: Report ID or number
- cohort: Patient cohort or population
- sample_type: Type of sample (blood, saliva, etc.)
- sample_collection_date: When sample was collected
- sample_received_date: When sample was received
- processed_date: When sample was processed
- ordering_clinician: Name of ordering physician/clinician
- npi: NPI number if available
- indication_for_testing: Reason for testing

Return ONLY a valid JSON object with these fields. If a field is not found, use null.

Text content:
{content}

JSON:
"""
    
    def _create_pgx_prompt(self, content: str) -> str:
        """Create prompt for PGX data extraction."""
        genes_list = ", ".join(PGX_GENES)
        
        return f"""
You are a pharmacogenomics expert. Extract PGX gene data from the following text content.

Look for these 13 genes: {genes_list}

For each gene found, extract:
- gene: Gene name (exactly as listed above)
- genotype: The genotype/allele information
- metabolizer_status: Metabolizer status (e.g., Normal Metabolizer, Poor Metabolizer, etc.)

Return a JSON array with objects for ALL 13 genes. If a gene is not found, use "Not found" for both genotype and metabolizer_status.

Text content:
{content}

JSON:
"""
    
    def _call_llm(self, prompt: str) -> str:
        """Call Azure OpenAI with the given prompt."""
        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=[
                    {"role": "system", "content": "You are a precise medical document parser. Always return valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=2000
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error calling Azure OpenAI: {e}")
            raise
    
    def _parse_patient_response(self, response: str) -> PatientInfo:
        """Parse LLM response into PatientInfo object."""
        try:
            # Clean response to extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            return PatientInfo(**data)
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error parsing patient response: {e}")
            return PatientInfo()
    
    def _parse_pgx_response(self, response: str) -> List[PgxGeneData]:
        """Parse LLM response into list of PgxGeneData objects."""
        try:
            # Clean response to extract JSON
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.endswith("```"):
                response = response[:-3]
            
            data = json.loads(response)
            
            # Ensure we have all 13 genes
            gene_data = {}
            for item in data:
                if isinstance(item, dict) and "gene" in item:
                    gene_data[item["gene"]] = item
            
            # Create list with all genes
            result = []
            for gene in PGX_GENES:
                if gene in gene_data:
                    result.append(PgxGeneData(**gene_data[gene]))
                else:
                    result.append(PgxGeneData(
                        gene=gene,
                        genotype="Not found",
                        metabolizer_status="Not found"
                    ))
            
            return result
        except (json.JSONDecodeError, TypeError) as e:
            logger.error(f"Error parsing PGX response: {e}")
            return [
                PgxGeneData(
                    gene=gene,
                    genotype="Not found",
                    metabolizer_status="Not found"
                )
                for gene in PGX_GENES
            ]


def extract_patient_info_with_llm(content: str) -> PatientInfo:
    """
    Extract patient information using Azure OpenAI LLM.
    
    Args:
        content: Text content from first page
        
    Returns:
        PatientInfo object
    """
    try:
        parser = AzureLLMParser()
        return parser.extract_patient_info_llm(content)
    except Exception as e:
        logger.error(f"LLM patient extraction failed: {e}")
        return PatientInfo()


def extract_pgx_data_with_llm(content: str) -> List[PgxGeneData]:
    """
    Extract PGX data using Azure OpenAI LLM.
    
    Args:
        content: Text content from PGX pages
        
    Returns:
        List of PgxGeneData objects
    """
    try:
        parser = AzureLLMParser()
        return parser.extract_pgx_data_llm(content)
    except Exception as e:
        logger.error(f"LLM PGX extraction failed: {e}")
        return [
            PgxGeneData(
                gene=gene,
                genotype="Not found",
                metabolizer_status="Not found"
            )
            for gene in PGX_GENES
        ]
