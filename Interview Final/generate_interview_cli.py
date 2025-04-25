import asyncio
import argparse
import logging
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from pydantic import SecretStr

# Ensure the project root is in the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root))

# Import necessary modules after path setup
from agents.parser_agent import ParserAgent
from agents.interview_agent import InterviewAgent
from models.data_models import ParsedInput, InterviewGuide
import utils.log_config  # Initializes logging based on environment

logger = logging.getLogger(__name__)

def load_api_keys():
    """Load API keys from .env file and return them."""
    load_dotenv()
    non_reasoning_key = os.getenv("NON_REASONING_API_KEY")
    reasoning_key = os.getenv("REASONING_API_KEY")

    if not non_reasoning_key:
        logger.error("NON_REASONING_API_KEY not found in environment variables.")
        sys.exit(1)
    if not reasoning_key:
        logger.error("REASONING_API_KEY not found in environment variables.")
        sys.exit(1)

    return SecretStr(non_reasoning_key), reasoning_key

def read_markdown_file(file_path: str) -> str:
    """Read content from the specified markdown file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        logger.error(f"Error: Markdown file not found at {file_path}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading markdown file {file_path}: {e}")
        sys.exit(1)

async def main():
    """Main function to orchestrate the parsing and interview generation."""
    parser = argparse.ArgumentParser(description="Parse markdown and generate an interview guide.")
    parser.add_argument("markdown_file", help="Path to the input markdown file.")
    args = parser.parse_args()

    # --- Step 1: Load API Keys ---
    non_reasoning_api_key, reasoning_api_key = load_api_keys()

    # --- Step 2: Read Raw Markdown ---
    logger.info(f"Reading markdown file: {args.markdown_file}")
    markdown_content = read_markdown_file(args.markdown_file)
    logger.info("--- Raw Markdown Content Start ---")
    # Log only the first 500 chars to avoid flooding logs
    logger.info(markdown_content[:500] + ("..." if len(markdown_content) > 500 else ""))
    logger.info("--- Raw Markdown Content End ---")

    try:
        # --- Step 3: Parse Markdown using ParserAgent ---
        logger.info("Initializing ParserAgent...")
        parser_agent = ParserAgent(non_reasoning_api_key=non_reasoning_api_key)

        logger.info("Parsing markdown content...")
        parsed_input: ParsedInput = parser_agent.parse_markdown(markdown_content)

        logger.info("--- Parsed Input JSON Start ---")
        print(parsed_input.model_dump_json(indent=2))
        logger.info("--- Parsed Input JSON End ---")

        # --- Step 4: Generate Interview Guide using InterviewAgent ---
        logger.info("Initializing InterviewAgent...")
        interview_agent = InterviewAgent(reasoning_api_key=reasoning_api_key)

        logger.info("Generating interview guide...")
        # Remove await as the method is now synchronous
        interview_guide: InterviewGuide = interview_agent.generate_interview_guide(parsed_input)

        logger.info("--- Interview Guide JSON Start ---")
        print(interview_guide.model_dump_json(indent=2))
        logger.info("--- Interview Guide JSON End ---")

        logger.info("Interview guide generated successfully.")

    except Exception as e:
        logger.error(f"An error occurred during the process: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())
