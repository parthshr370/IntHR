from typing import Dict, Any, List, Tuple
from templates.form_template import STEP4_FIELDS

def validate_job_input(job_input: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate the job input data"""
    errors = []
    
    # Required fields
    required_fields = [
        "company_name",
        "cultural_fit_factors",
        "personality_traits",
        "work_experience",
        "technology_domain",
        "tools",
        "role_title",
        "core_responsibilities",
        "skills_competencies",
        "education_requirements",
        "specialized_role_focus"
    ]
    
    # Check for required fields
    for field in required_fields:
        if field not in job_input or not job_input[field]:
            errors.append(f"Missing required field: {field}")
    
    # Check for list fields
    list_fields = ["cultural_fit_factors", "personality_traits", "technology_domain", "tools"]
    for field in list_fields:
        if field in job_input and not isinstance(job_input[field], list):
            errors.append(f"Field {field} must be a list")
    
    # Validate specific fields
# Validate specific fields



    # Find the specialized_role_focus field
    role_focus_field = next(field for field in STEP4_FIELDS if field["key"] == "specialized_role_focus")
    valid_roles = role_focus_field["options"]

    if "specialized_role_focus" in job_input and job_input["specialized_role_focus"] not in valid_roles:
        errors.append(f"Invalid role focus: {job_input['specialized_role_focus']}")        
                
    if "employment_type" in job_input:
        valid_types = ["Full-Time", "Part-Time", "Contract", "Freelance"]
        if job_input["employment_type"] not in valid_types:
            errors.append(f"Invalid employment type: {job_input['employment_type']}")
    
    return len(errors) == 0, errors


def format_error_message(errors: List[str]) -> str:
    """Format error messages for display"""
    if not errors:
        return ""
        
    return "Please fix the following errors:\n" + "\n".join([f"- {error}" for error in errors])