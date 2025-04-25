#!/usr/bin/env python3
import argparse
import json
import sys
from dotenv import load_dotenv

# Import project modules
from chains.workflow import run_workflow
from utils.validators import format_error_message

# Load environment variables
load_dotenv()

def main():
    parser = argparse.ArgumentParser(description="Job Description Generator CLI")
    parser.add_argument("--input", "-i", help="Input JSON file with job details (required)")
    parser.add_argument("--output", "-o", help="Output file for the generated job description (optional)")
    args = parser.parse_args()
    
    if not args.input:
        print("Error: Input file is required")
        print("Usage: python simplified_cli.py --input example_input.json [--output job_description.md]")
        sys.exit(1)
    
    # Load job details from JSON file
    try:
        with open(args.input, 'r') as f:
            job_input = json.load(f)
        
        print("Generating job description from input file...")
        
        # Run the workflow
        result = run_workflow(job_input)
        
        if result["errors"]:
            print("❌ Errors occurred:")
            print(format_error_message(result["errors"]))
            sys.exit(1)
        else:
            print("✅ Job Description Generated Successfully:")
            
            if args.output:
                with open(args.output, 'w') as f:
                    f.write(result["job_description"])
                print(f"Job description saved to {args.output}")
            else:
                print("\n" + "=" * 50)
                print(result["job_description"])
                print("=" * 50)
            
            print("\nPosting Simulation Results (No actual posting):")
            for platform, post_result in result["posting_results"].items():
                status = "✅" if post_result.get("success") else "❌"
                print(f"{status} {platform.capitalize()}: {post_result.get('message')}")
    
    except FileNotFoundError:
        print(f"Error: Input file {args.input} not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print(f"Error: Input file {args.input} is not valid JSON")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()