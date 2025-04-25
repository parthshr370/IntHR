from typing import Dict, Any, List
from agents.jd_generator import JDGenerator, JobInput
from agents.job_poster import JobPoster
from utils.validators import validate_job_input
from config.settings import PREVIEW_MODE

def run_workflow(job_input: Dict[str, Any]) -> Dict[str, Any]:
    """
    Run the job description generation workflow.
    
    Args:
        job_input: Dictionary containing job input data
        
    Returns:
        Dictionary with the workflow results
    """
    # Initialize agents
    jd_generator = JDGenerator()
    
    # Get preview mode from settings (or use default True)
    preview_mode = PREVIEW_MODE
    job_poster = JobPoster(preview_mode=preview_mode)
    
    # Initialize the state
    state = {
        "job_input": job_input,
        "job_description": "",
        "posting_results": {},
        "errors": [],
        "status": "started"
    }
    
    # Step 1: Validate input
    is_valid, validation_errors = validate_job_input(job_input)
    if not is_valid:
        state["errors"] = validation_errors
        state["status"] = "input_invalid"
        return state
    
    state["status"] = "input_valid"
    
    # Step 2: Generate job description
    try:
        # Convert dict to JobInput
        job_input_obj = JobInput(**job_input)
        
        # Generate job description
        job_description = jd_generator.generate_jd(job_input_obj)
        
        state["job_description"] = job_description
        state["status"] = "jd_generated"
    except Exception as e:
        state["errors"].append(f"JD Generation Error: {str(e)}")
        state["status"] = "error"
        return state
    
    # Step 3: Post job to platforms
    try:
        # Use job_poster with the preview_mode setting
        posting_results = job_poster.post_job(job_description)
        
        state["posting_results"] = posting_results
        state["status"] = "completed"
    except Exception as e:
        state["errors"].append(f"Job Posting Error: {str(e)}")
        state["status"] = "error"
    
    return state