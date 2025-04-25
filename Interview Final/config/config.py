import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).parent.parent
TESTS_DIR = BASE_DIR / "tests"
OUTPUT_DIR = BASE_DIR / "output"

# Create output directory if it doesn't exist
OUTPUT_DIR.mkdir(exist_ok=True)

# API Keys
REASONING_API_KEY = os.getenv("REASONING_API_KEY")
NON_REASONING_API_KEY = os.getenv("NON_REASONING_API_KEY")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "interview_module.log")
LOG_PATH = BASE_DIR / LOG_FILE

# Test files
SAMPLE_INPUT_FILE = TESTS_DIR / "sample_input.md"
PARSER_OUTPUT_FILE = TESTS_DIR / "parser_output.json"
INTERVIEW_OUTPUT_FILE = TESTS_DIR / "interview_guide.json"

# Validation
if not REASONING_API_KEY:
    raise ValueError("REASONING_API_KEY not set in environment")
if not NON_REASONING_API_KEY:
    raise ValueError("NON_REASONING_API_KEY not set in environment") 