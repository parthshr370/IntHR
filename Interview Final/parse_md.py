import os
import sys
import json
from dotenv import load_dotenv

# Ensure the project root is in the Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from agents.parser_agent import ParserAgent
from models.data_models import ParsedInput
from utils.log_config import logger


def main(file_path: str):
    """Parses a markdown file using ParserAgent and prints the JSON output."""
    load_dotenv() # Load environment variables from .env file

    api_key = os.getenv("NON_REASONING_API_KEY")
    if not api_key:
        logger.error("Error: NON_REASONING_API_KEY not found in environment variables.")
        print("Error: NON_REASONING_API_KEY not found. Please set it in your .env file.")
        sys.exit(1)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
    except FileNotFoundError:
        logger.error(f"Error: File not found at {file_path}")
        print(f"Error: File not found at {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        print(f"Error reading file {file_path}: {e}")
        sys.exit(1)

    try:
        logger.info("Initializing ParserAgent...")
        # Note: ParserAgent uses hardcoded base_url and model internally
        parser_agent = ParserAgent(non_reasoning_api_key=api_key)
        
        logger.info(f"Parsing markdown content from {file_path}...")
        parsed_data: ParsedInput = parser_agent.parse_markdown(markdown_content)
        
        logger.info("Parsing complete. Outputting JSON...")
        # Convert the Pydantic model to a JSON string
        json_output = parsed_data.model_dump_json(indent=2)
        
        print("\n--- Parsed JSON Output ---")
        print(json_output)
        print("--- End of Output ---")

    except Exception as e:
        logger.error(f"An error occurred during parsing: {e}", exc_info=True)
        print(f"An error occurred during parsing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    markdown_file = "sample.md" # File to parse
    main(markdown_file)
