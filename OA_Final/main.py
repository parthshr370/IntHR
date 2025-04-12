# main.py

import os
from dotenv import load_dotenv
from typing import Dict, Any, Optional
import asyncio
import json
import logging
import sys
from utils.content_analyzer import ContentAnalyzer
from agents.question_generator import QuestionGenerator
from agents.assessment_agent import AssessmentAgent
from models.data_models import Assessment, AssessmentResult
from pathlib import Path

# Setup logger for this module
logger = logging.getLogger(__name__)

class OAModule:
    """Enhanced Online Assessment Module with simplified parsing"""
    
    def __init__(self):
        """Initialize OA Module with necessary components"""
        logger.info("Initializing OAModule...")
        # Try to load .env from multiple possible locations
        env_paths = [
            '.env',
            '../.env',
            Path(__file__).parent / '.env',
            Path(__file__).parent.parent / '.env'
        ]
        
        env_loaded = False
        for env_path in env_paths:
            if Path(env_path).exists():
                logger.info(f"Loading .env from: {env_path}")
                load_dotenv(env_path)
                env_loaded = True
                break
        
        if not env_loaded:
            logger.warning("No .env file found")
        
        # Get API keys with fallback values
        self.non_reasoning_key = os.getenv("NON_REASONING_API_KEY")
        self.reasoning_key = os.getenv("REASONING_API_KEY")
        
        if not self.non_reasoning_key or not self.reasoning_key:
            logger.warning("API keys not found in environment variables from .env, checking direct environment...")
            # Try to create keys from existing environment variables
            self.non_reasoning_key = os.environ.get("NON_REASONING_API_KEY")
            self.reasoning_key = os.environ.get("REASONING_API_KEY")
            
            if not self.non_reasoning_key or not self.reasoning_key:
                logger.error(
                    "API keys not found. Please ensure NON_REASONING_API_KEY and "
                    "REASONING_API_KEY are set in your .env file or environment variables"
                )
                raise ValueError("API keys not found.")
            
        logger.info("API keys loaded successfully.")
        # Initialize components
        logger.info("Initializing components (ContentAnalyzer, QuestionGenerator, AssessmentAgent)...")
        self.analyzer = ContentAnalyzer(self.non_reasoning_key)
        self.generator = QuestionGenerator(self.non_reasoning_key)
        self.assessor = AssessmentAgent(self.reasoning_key)
        logger.info("OAModule initialized successfully.")
        
    async def process_input(self, markdown_content: str) -> Assessment:
        """Process markdown input and generate assessment"""
        logger.info("Starting input processing...")
        try:
            # Get complete analysis from the content analyzer
            logger.debug("Analyzing content...")
            analysis = await self.analyzer.analyze_content(markdown_content)
            logger.debug(f"Content analysis received: {analysis}")
            
            # Extract key information for question generation
            level = analysis["candidate_details"]["experience_level"]
            matching_skills = analysis["skill_gap_analysis"]["matching_skills"]
            relevant_experience = analysis["candidate_details"]["relevant_experience"]
            
            logger.info(f"Candidate level determined: {level}")
            logger.info(f"Matched skills: {matching_skills}")
            
            # Generate assessment
            logger.info("Generating assessment...")
            assessment = await self.generator.generate_assessment(
                candidate_name=analysis["candidate_details"]["name"],
                job_title=analysis["job_details"]["title"],
                skills=matching_skills,
                experience=relevant_experience,
                level=level,
                job_requirements=analysis["job_details"],
                candidate_profile=analysis["candidate_details"]
            )
            logger.info("Assessment generation complete.")
            return assessment
            
        except Exception as e:
            logger.error(f"Error processing input: {str(e)}", exc_info=True)
            raise
        
    async def evaluate_responses(
        self,
        assessment: Assessment,
        responses: Dict[str, str]
    ) -> AssessmentResult:
        """Evaluate candidate responses"""
        logger.info("Starting response evaluation...")
        try:
            result = await self.assessor.evaluate_assessment(assessment, responses)
            logger.info("Response evaluation complete.")
            return result
        except Exception as e:
            logger.error(f"Error evaluating responses: {str(e)}", exc_info=True)
            raise
        
    def generate_report(self, result: AssessmentResult) -> str:
        """Generate human-readable report"""
        logger.info("Generating summary report...")
        try:
            report = self.assessor.generate_summary_report(result)
            logger.info("Summary report generation complete.")
            return report
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}", exc_info=True)
            raise

async def main(markdown_file: str, response_file: Optional[str] = None):
    """Main function to run the OA module"""
    logger.info(f"Starting OA module execution for file: {markdown_file}")
    try:
        # Initialize module
        oa_module = OAModule()
        
        # Read input markdown
        logger.info(f"Reading markdown file: {markdown_file}")
        with open(markdown_file, 'r', encoding='utf-8') as f:
            markdown_content = f.read()
        logger.info("Markdown file read successfully.")
            
        # Generate assessment
        assessment = await oa_module.process_input(markdown_content)
        logger.info(f"Generated assessment with {len(assessment.coding_questions)} coding, "
                    f"{len(assessment.system_design_questions)} system design, and "
                    f"{len(assessment.behavioral_questions)} behavioral questions.")
        
        # If response file provided, evaluate responses
        if response_file:
            logger.info(f"Response file provided: {response_file}. Evaluating responses.")
            with open(response_file, 'r', encoding='utf-8') as f:
                responses = json.load(f)
            logger.info("Responses loaded.")
                
            result = await oa_module.evaluate_responses(assessment, responses)
            report = oa_module.generate_report(result)
            logger.info("\n--- Assessment Report ---\n" + report)
            
        else:
            logger.info("No response file provided. Skipping evaluation and report generation.")
            
        logger.info(f"OA module execution finished successfully for file: {markdown_file}")
        return assessment
        
    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error running OA module: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    import logging  # Import logging
    
    # --- LOGGING CONFIG ADDED ---
    logging.basicConfig(
        level=logging.DEBUG, 
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filename='app.log', 
        filemode='a' # Append to the log file
    )
    # --- END LOGGING CONFIG ---
    
    logger.info("Parsing command line arguments...")
    parser = argparse.ArgumentParser(description="Run Online Assessment Module")
    parser.add_argument("markdown_file", help="Path to input markdown file")
    parser.add_argument("--responses", help="Path to JSON file with responses")
    
    args = parser.parse_args()
    logger.info(f"Arguments parsed: markdown_file={args.markdown_file}, responses={args.responses}")
    
    logger.info("Starting asyncio event loop...")
    asyncio.run(main(args.markdown_file, args.responses))
    logger.info("Asyncio event loop finished.")