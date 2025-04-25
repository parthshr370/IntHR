import logging
import re
import json
from typing import Dict, Any, Optional

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.info("Initializing md_parser")

class MarkdownParser:
    """Ultra-simplified utility that extracts raw text and sections from markdown"""
    
    @staticmethod
    def extract_raw_text(content: str) -> str:
        """
        Return raw text from markdown without removing any syntax.
        (Previously removed markdown syntax elements)
        """
        # Just return the original content
        return content

    @staticmethod
    def extract_json_sections(content: str) -> Dict[str, Any]:
        """
        Extract JSON sections from markdown content
        """
        try:
            # Extract JSON blocks
            json_blocks = re.findall(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            
            # Parse each JSON block
            parsed_sections = {}
            for block in json_blocks:
                try:
                    data = json.loads(block)
                    # Use the first key as section name if it's a dict
                    if isinstance(data, dict):
                        for key, value in data.items():
                            parsed_sections[key] = value
                            break
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON block: {block[:100]}...")
                    continue
                    
            return parsed_sections
            
        except Exception as e:
            logger.error(f"Error extracting JSON sections: {str(e)}")
            return {}
    
    @staticmethod
    def extract_section(content: str, section_name: str) -> Optional[str]:
        """
        Extract a specific section from markdown content
        """
        try:
            # Look for section header
            pattern = rf"#+\s*{section_name}\s*\n(.*?)(?=\n#+\s*|$)"
            match = re.search(pattern, content, re.DOTALL)
            
            if match:
                return match.group(1).strip()
            return None
            
        except Exception as e:
            logger.error(f"Error extracting section {section_name}: {str(e)}")
            return None 