# config.py

import os
from pathlib import Path
from dotenv import load_dotenv
import logging
import logging.handlers # Import handlers

# --- Enhanced Logging Setup ---
LOG_FILENAME = 'app.log'
LOG_LEVEL = logging.INFO  # Default level
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# Configure root logger
logger = logging.getLogger() # Get root logger
logger.setLevel(LOG_LEVEL)

# Clear existing handlers (optional, prevents duplicate logs if run multiple times)
if logger.hasHandlers():
    logger.handlers.clear()

# Create formatter
formatter = logging.Formatter(LOG_FORMAT, datefmt=LOG_DATE_FORMAT)

# Console Handler
ch = logging.StreamHandler()
ch.setLevel(LOG_LEVEL)
ch.setFormatter(formatter)
logger.addHandler(ch)

# File Handler (rotating)
# Rotate log file when it reaches 5MB, keep 3 backup logs
fh = logging.handlers.RotatingFileHandler(LOG_FILENAME, maxBytes=5*1024*1024, backupCount=3)
fh.setLevel(LOG_LEVEL)
fh.setFormatter(formatter)
logger.addHandler(fh)

# Reduce verbosity of noisy libraries (optional)
# logging.getLogger("httpx").setLevel(logging.WARNING)
# logging.getLogger("httpcore").setLevel(logging.WARNING)

logger.info("--- Logging initialized ---")
# --- End Enhanced Logging Setup ---


# Load environment variables
logger.info("Loading environment variables...")
load_dotenv()
logger.info("Environment variables loaded.")

# API Keys
NON_REASONING_API_KEY = os.getenv("NON_REASONING_API_KEY")
REASONING_API_KEY = os.getenv("REASONING_API_KEY")

# Validate API keys
logger.info("Validating API keys...")
if not NON_REASONING_API_KEY or not NON_REASONING_API_KEY.startswith('sk-or-'):
    logger.error("Invalid or missing NON_REASONING_API_KEY format. Must start with 'sk-or-'")
    
if not REASONING_API_KEY or not REASONING_API_KEY.startswith('sk-or-'):
    logger.error("Invalid or missing REASONING_API_KEY format. Must start with 'sk-or-'")
else:
    logger.info("API keys validated.")


# Model configurations
logger.info("Loading model configurations...")
NON_REASONING_MODEL = os.getenv("NON_REASONING_MODEL", "google/gemini-pro")
REASONING_MODEL = os.getenv("REASONING_MODEL", "gpt-3.5-turbo")
logger.info(f"NON_REASONING_MODEL set to: {NON_REASONING_MODEL}")
logger.info(f"REASONING_MODEL set to: {REASONING_MODEL}")


# --- Assessment Configuration ---
logger.info("Loading assessment configuration...")
ASSESSMENT_CONFIG = {
    "junior": {
        "coding_questions": 5,
        "system_design_questions": 5,
        "behavioral_questions": 5,
        "passing_score_percentage": 65
    },
    "mid": {
        "coding_questions": 5,
        "system_design_questions": 5,
        "behavioral_questions": 5,
        "passing_score_percentage": 70
    },
    "senior": {
        "coding_questions": 5,
        "system_design_questions": 5,
        "behavioral_questions": 5,
        "passing_score_percentage": 75
    },
    "passing_score_percentage": 70 # Default if level not found
}

QUESTION_WEIGHTS = {
    "coding": {
        "junior": {"min": 6, "max": 12},
        "mid": {"min": 8, "max": 15},
        "senior": {"min": 10, "max": 20}
    },
    "system_design": {
        "junior": {"min": 8, "max": 15},
        "mid": {"min": 10, "max": 18},
        "senior": {"min": 12, "max": 25}
    },
    "behavioral": {
        "junior": {"min": 4, "max": 10},
        "mid": {"min": 6, "max": 12},
        "senior": {"min": 8, "max": 15}
    }
}
logger.info(f"Assessment config loaded: {ASSESSMENT_CONFIG}")
logger.info(f"Question weights loaded: {QUESTION_WEIGHTS}")
# --- End Assessment Configuration ---


# API Configuration
API_CONFIG = {
    "non_reasoning": {
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 60,
        "max_retries": 3,
        "headers": {
            "HTTP-Referer": "http://localhost:8501",  # Required for OpenRouter
            "X-Title": "HR Portal Assessment"  # Optional but recommended
        }
    },
    "reasoning": {
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 90,
        "max_retries": 3
    }
}

logger.info(f"API Configuration loaded: {API_CONFIG}")

# Ensure required directories exist
TEMPLATES_DIR = Path(__file__).parent / "templates"
logger.info(f"Ensuring templates directory exists: {TEMPLATES_DIR}")
TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)
logger.info("Templates directory checked/created.")