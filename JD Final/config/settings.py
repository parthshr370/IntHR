import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# LLM Provider settings
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")  # "openai" or "gemini"
LLM_MODEL = os.getenv("LLM_MODEL", "gemini-pro")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# Twitter API keys
TWITTER_API_KEY = os.getenv("TWITTER_API_KEY")
TWITTER_API_SECRET = os.getenv("TWITTER_API_SECRET")
TWITTER_ACCESS_TOKEN = os.getenv("TWITTER_ACCESS_TOKEN")
TWITTER_ACCESS_SECRET = os.getenv("TWITTER_ACCESS_SECRET")

# Google Jobs API
GOOGLE_JOBS_SERVICE_ACCOUNT_PATH = os.getenv("GOOGLE_JOBS_SERVICE_ACCOUNT_PATH")
GOOGLE_CLOUD_PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT_ID")
GOOGLE_JOBS_TENANT_ID = os.getenv("GOOGLE_JOBS_TENANT_ID")
GOOGLE_JOBS_COMPANY_ID = os.getenv("GOOGLE_JOBS_COMPANY_ID")

# Naukri API keys (placeholder)
NAUKRI_API_KEY = os.getenv("NAUKRI_API_KEY")

# Upwork API keys (placeholder)
UPWORK_API_KEY = os.getenv("UPWORK_API_KEY")
UPWORK_API_SECRET = os.getenv("UPWORK_API_SECRET")

# LLM Settings
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4")
LLM_TEMPERATURE = float(os.getenv("LLM_TEMPERATURE", "0.7"))

# Application Settings
DEBUG = os.getenv("DEBUG", "False").lower() == "true"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
PREVIEW_MODE = os.getenv("PREVIEW_MODE", "True").lower() == "true"

# Job Platforms
JOB_PLATFORMS = {
    "twitter": {
        "enabled": os.getenv("TWITTER_ENABLED", "False").lower() == "true",
        "api_url": "https://api.twitter.com/2/tweets",
    },
    "naukri": {
        "enabled": os.getenv("NAUKRI_ENABLED", "False").lower() == "true",
        "api_url": "https://api.naukri.com/v1/jobs",
    },
    "google_jobs": {
        "enabled": os.getenv("GOOGLE_JOBS_ENABLED", "False").lower() == "true",
        "api_url": "https://jobs.googleapis.com/v4/jobs",
    },
    "upwork": {
        "enabled": os.getenv("UPWORK_ENABLED", "False").lower() == "true",
        "api_url": "https://api.upwork.com/v1/jobs/postings",
    }
}