import os
import asyncio
import json
import argparse
from pathlib import Path
from dotenv import load_dotenv

from agents import ParserAgent, InterviewAgent
from utils import setup_logging

# Load environment variables
load_dotenv()

# Setup logging
setup_logging(
    level=os.getenv("LOG_LEVEL", "INFO"),
    log_file=os.getenv("LOG_FILE", "interview_module.log")
)

async def main():
    """Main function to run the interview module"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Generate interview guide from OA markdown output")
    parser.add_argument("markdown_file", help="Path to the input markdown file")
    parser.add_argument("--output", "-o", default="output", help="Output directory for results")
    args = parser.parse_args()
    
    try:
        # Get API keys
        non_reasoning_key = os.getenv("NON_REASONING_API_KEY")
        reasoning_key = os.getenv("REASONING_API_KEY")
        
        if not non_reasoning_key or not reasoning_key:
            raise ValueError("API keys not found in environment variables")
            
        # Initialize agents
        parser_agent = ParserAgent(non_reasoning_api_key=non_reasoning_key)
        interview = InterviewAgent(reasoning_api_key=reasoning_key)
        
        # Read input markdown
        input_file = Path(args.markdown_file)
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")
            
        with open(input_file, "r") as f:
            content = f.read()
            
        # Step 1: Parse input
        print("\n1. Parsing input markdown...")
        parsed_input = parser_agent.parse_markdown(content)
        
        # Save parsed output
        output_dir = Path(args.output)
        output_dir.mkdir(exist_ok=True)
        
        with open(output_dir / "parsed_input.json", "w") as f:
            json.dump(parsed_input.dict(), f, indent=2)
        print(f"Parsed input saved to {output_dir}/parsed_input.json")
        
        # Step 2: Generate interview guide
        print("\n2. Generating interview guide...")
        guide = await interview.generate_interview_guide(parsed_input)
        
        # Save interview guide
        with open(output_dir / "interview_guide.json", "w") as f:
            json.dump(guide.dict(), f, indent=2)
        print(f"Interview guide saved to {output_dir}/interview_guide.json")
        
        # Print summary
        print("\nSUMMARY")
        print("=======")
        print(f"Candidate: {guide.candidate_name}")
        print(f"Position: {guide.job_title}")
        print(f"Total Score Required: {guide.passing_score}/{guide.total_score}")
        print("\nInterview Sections:")
        for section in guide.sections:
            print(f"- {section.name}: {len(section.questions)} questions")
            
    except Exception as e:
        print(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 