from typing import Dict, Any, Optional
import json
from ..prompts.citation_prompts import CitationPrompts
import os
import httpx
from dspy.retrieve import read_jsonl
import dspy

class LLMHandler:
    def __init__(self):
        # Initialize LLM backend (Ollama by default)
        self.ollama_base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.getenv('CITATION_LLM_MODEL', 'llama2')
        self.prompts = CitationPrompts()
        
    async def enhance_metadata(self, text: str, doc_type: str, initial_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Use LLM to enhance extracted metadata."""
        try:
            # Generate prompt
            prompt = self.prompts.get_metadata_extraction_prompt(text, doc_type)
            
            # Get LLM completion
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    llm_metadata = self._parse_llm_response(response.json()['response'])
                    
                    # Merge with initial metadata, preferring LLM results for missing fields
                    enhanced_metadata = {**initial_metadata}
                    for key, value in llm_metadata.items():
                        if key not in enhanced_metadata or not enhanced_metadata[key]:
                            enhanced_metadata[key] = value
                            
                    return enhanced_metadata
                    
        except Exception as e:
            print(f"Error enhancing metadata with LLM: {e}")
            return initial_metadata

    async def format_citation(self, metadata: Dict[str, Any], style: str = "chicago") -> str:
        """Format metadata as a citation string using LLM."""
        try:
            prompt = self.prompts.get_citation_format_prompt(metadata, style)
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_base_url}/api/generate",
                    json={
                        "model": self.model,
                        "prompt": prompt,
                        "stream": False
                    }
                )
                
                if response.status_code == 200:
                    return response.json()['response'].strip()
                    
        except Exception as e:
            print(f"Error formatting citation with LLM: {e}")
            # Fallback to basic formatting
            return self._basic_citation_format(metadata)

    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """Parse LLM response into a metadata dictionary."""
        try:
            # Try to parse as JSON first
            if response.strip().startswith('{'):
                return json.loads(response)
                
            # Otherwise parse key-value pairs
            metadata = {}
            lines = response.strip().split('\n')
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    key = key.strip().lower().replace(' ', '_')
                    value = value.strip()
                    if value and value != 'N/A':
                        metadata[key] = value
            return metadata
            
        except Exception as e:
            print(f"Error parsing LLM response: {e}")
            return {}

    def _basic_citation_format(self, metadata: Dict[str, Any]) -> str:
        """Basic citation formatting as fallback."""
        doc_type = metadata.get('citation_type', '')
        
        if doc_type == 'book':
            return f"{metadata.get('author', '')}. {metadata.get('year', '')}. {metadata.get('title', '')}. {metadata.get('location', '')}: {metadata.get('publisher', '')}."
        elif doc_type == 'article':
            return f"{metadata.get('author', '')}. {metadata.get('year', '')}. \"{metadata.get('title', '')}.\" {metadata.get('journal', '')} {metadata.get('pages', '')}."
        else:
            # Basic format for other types
            return f"{metadata.get('author', '')}. {metadata.get('year', '')}. {metadata.get('title', '')}."