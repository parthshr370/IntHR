#!/usr/bin/env python3

import os
import sys
import logging
import requests
from pathlib import Path
from dotenv import load_dotenv
import asyncio
from langchain_openai import ChatOpenAI

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class APIKeyTester:
    def __init__(self):
        self.non_reasoning_key = None
        self.reasoning_key = None
        self.load_env()

    def load_env(self):
        """Load environment variables from .env file"""
        env_paths = ['.env', '../.env', Path(__file__).parent / '.env']
        env_loaded = False

        for env_path in env_paths:
            if Path(env_path).exists():
                logger.info(f"Found .env file at: {env_path}")
                load_dotenv(env_path)
                env_loaded = True
                break

        if not env_loaded:
            logger.error("No .env file found!")
            sys.exit(1)

        # Get API keys
        self.non_reasoning_key = os.getenv("NON_REASONING_API_KEY")
        self.reasoning_key = os.getenv("REASONING_API_KEY")

    def validate_key_format(self):
        """Validate API key formats"""
        issues = []

        if not self.non_reasoning_key:
            issues.append("NON_REASONING_API_KEY is missing")
        elif not self.non_reasoning_key.startswith('sk-or-'):
            issues.append("NON_REASONING_API_KEY should start with 'sk-or-'")

        if not self.reasoning_key:
            issues.append("REASONING_API_KEY is missing")
        elif not self.reasoning_key.startswith('sk-or-'):
            issues.append("REASONING_API_KEY should start with 'sk-or-'")

        return issues

    async def test_openrouter_api(self):
        """Test OpenRouter API connection"""
        try:
            logger.info("Testing OpenRouter API connection...")
            
            # Initialize ChatOpenAI with OpenRouter
            chat = ChatOpenAI(
                model="google/gemini-pro",
                temperature=0.7,
                openai_api_key=self.non_reasoning_key,
                openai_api_base="https://openrouter.ai/api/v1"
            )

            # Test with a simple query
            response = await chat.ainvoke("Test connection")
            logger.info("OpenRouter API test successful!")
            return True

        except Exception as e:
            logger.error(f"OpenRouter API test failed: {str(e)}")
            return False

    async def test_reasoning_openrouter_api(self):
        """Test Reasoning Model API connection via OpenRouter"""
        try:
            logger.info("Testing Reasoning Model API connection via OpenRouter...")
            
            # Initialize ChatOpenAI with OpenRouter for the reasoning model
            chat = ChatOpenAI(
                model="gpt-3.5-turbo",
                temperature=0.7,
                openai_api_key=self.reasoning_key,
                openai_api_base="https://openrouter.ai/api/v1"
            )

            # Test with a simple query
            response = await chat.ainvoke("Test connection")
            logger.info("Reasoning Model OpenRouter API test successful!")
            return True

        except Exception as e:
            logger.error(f"Reasoning Model OpenRouter API test failed: {str(e)}")
            return False

    def print_summary(self, format_issues, non_reasoning_or_success, reasoning_or_success):
        """Print test summary"""
        print("\n=== API Key Test Summary ===")
        
        if format_issues:
            print("\n❌ Format Issues:")
            for issue in format_issues:
                print(f"  - {issue}")
        else:
            print("\n✅ API Key formats are valid")

        print("\nAPI Connection Tests (via OpenRouter):")
        print(f"  Non-Reasoning Model API: {'✅ Success' if non_reasoning_or_success else '❌ Failed'}")
        print(f"  Reasoning Model API: {'✅ Success' if reasoning_or_success else '❌ Failed'}")

        if not (non_reasoning_or_success and reasoning_or_success):
            print("\nTroubleshooting Tips:")
            print("1. Verify your API keys are correct and start with 'sk-or-'")
            print("2. Check your internet connection")
            print("3. Ensure your OpenRouter keys have sufficient credits")
            print("4. Verify OpenRouter service status:")
            print("   - OpenRouter: https://openrouter.ai/status")

async def main():
    tester = APIKeyTester()
    
    # Test key formats
    format_issues = tester.validate_key_format()
    
    # Test API connections
    non_reasoning_success = await tester.test_openrouter_api()
    reasoning_success = await tester.test_reasoning_openrouter_api()
    
    # Print summary
    tester.print_summary(format_issues, non_reasoning_success, reasoning_success)

    # Exit with appropriate status code
    if format_issues or not (non_reasoning_success and reasoning_success):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        sys.exit(1)