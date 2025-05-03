from typing import Dict, Any, Literal
import yaml
import json
import csv
from datetime import datetime
from io import StringIO

OutputFormat = Literal['yaml', 'json', 'csv']

class CitationFormatter:
    def __init__(self, style: str = "chicago"):
        self.style = style
        
    def format_output(self, metadata: Dict[str, Any], output_format: OutputFormat = 'yaml') -> str:
        """Format citation metadata in the specified output format."""
        # Clean up metadata before formatting
        cleaned_metadata = self._clean_metadata(metadata)
        
        if output_format == 'yaml':
            return yaml.dump(cleaned_metadata, allow_unicode=True, sort_keys=False)
        elif output_format == 'json':
            return json.dumps(cleaned_metadata, ensure_ascii=False, indent=2)
        elif output_format == 'csv':
            output = StringIO()
            writer = csv.DictWriter(output, fieldnames=cleaned_metadata.keys())
            writer.writeheader()
            writer.writerow(cleaned_metadata)
            return output.getvalue()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _clean_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate metadata fields."""
        cleaned = {}
        
        # Required fields for all types
        required_fields = ['title', 'type', 'citation_type']
        
        # Add required fields first
        for field in required_fields:
            cleaned[field] = metadata.get(field, '')
            
        # Handle author name formatting
        if 'author' in metadata:
            author = metadata['author']
            if ',' not in author:  # If not already in "Last, First" format
                parts = author.split()
                if len(parts) > 1:
                    cleaned['author'] = f"{parts[-1]}, {' '.join(parts[:-1])}"
                else:
                    cleaned['author'] = author
        
        # Add other fields
        for key, value in metadata.items():
            if key not in cleaned:
                cleaned[key] = value
                
        # Format dates consistently
        if 'date' in cleaned:
            try:
                date = datetime.strptime(cleaned['date'], '%Y-%m-%d')
                cleaned['date'] = date.strftime('%Y-%m-%d')
            except ValueError:
                pass  # Keep original format if parsing fails
                
        # Ensure page numbers are properly formatted
        if 'pages' in cleaned and not cleaned['pages'].startswith('pp.'):
            cleaned['pages'] = f"pp. {cleaned['pages']}"
            
        return cleaned

    def save_to_file(self, metadata: Dict[str, Any], output_path: str, output_format: OutputFormat = 'yaml') -> None:
        """Save citation metadata to a file."""
        formatted_output = self.format_output(metadata, output_format)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(formatted_output)