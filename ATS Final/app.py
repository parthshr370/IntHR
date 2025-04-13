import streamlit as st
import tempfile
import os
import json
from config.config import MODELS, SUPPORTED_FILE_TYPES
from utils.file_handlers import FileHandler
from utils.text_preprocessing import TextPreprocessor
from agents.resume_parsing_agent import ResumeParsingAgent
from agents.job_matching_agent import JobMatchingAgent
from agents.decision_feedback_agent import DecisionFeedbackAgent
from ui.dashboard import create_analysis_dashboard
from ui.candidate_summary import create_candidate_summary_page
from ui.social_media_analysis import create_social_media_analysis_section, create_screening_summary, create_verification_progress
from ui.resume_highlight import display_resume_with_feedback
from dotenv import load_dotenv
import base64 # Added for potential future use if needed for downloads, though st.download handles text well

# --- Import Pydantic Models ---
from models.resume_models import ParsedResume
from models.job_match_models import MatchAnalysis
from models.decision_models import DecisionFeedback

# Load environment variables from .env file
load_dotenv()

# Ensure API keys are loaded (handle potential missing keys)
NON_REASONING_API_KEY = os.getenv("NON_REASONING_API_KEY")
REASONING_API_KEY = os.getenv("REASONING_API_KEY")

# Update MODELS dictionary with loaded keys
if NON_REASONING_API_KEY:
    MODELS['non_reasoning']['api_key'] = NON_REASONING_API_KEY
# Removed error message for cleaner UI if key is missing during dev
# else:
#     st.error("Error: NON_REASONING_API_KEY not found in .env file. Please set it.")

if REASONING_API_KEY:
    MODELS['reasoning']['api_key'] = REASONING_API_KEY
# Removed error message for cleaner UI
# else:
#     st.error("Error: REASONING_API_KEY not found in .env file. Please set it.")

# --- Page Configuration ---
st.set_page_config(
    page_title="ATS Portal: Resume Analyzer & Job Matcher",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Global State Management ---
def initialize_session_state():
    """Initialize session state variables if they don't exist"""
    if 'parsed_resume' not in st.session_state:
        st.session_state.parsed_resume = ParsedResume()
    if 'match_analysis' not in st.session_state:
        st.session_state.match_analysis = MatchAnalysis()
    if 'decision' not in st.session_state:
        st.session_state.decision = DecisionFeedback()
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""
    if 'active_tab' not in st.session_state:
        st.session_state.active_tab = "Job Description"

# --- Helper Function for Markdown Download ---
def create_download_markdown(jd, resume, analysis, decision):
    """Generates a Markdown string containing JD, parsed resume (JSON), and analysis (JSON)."""
    markdown_content = "# Analysis Report\\n\\n"

    markdown_content += "## Job Description\\n\\n"
    if jd:
        # Indent JD for better readability within markdown code block
        indented_jd = "\\n".join(["  " + line for line in jd.splitlines()])
        markdown_content += f"```\\n{indented_jd}\\n```\\n\\n"
    else:
        markdown_content += "Job Description not provided.\\n\\n"

    markdown_content += "## Parsed Resume (JSON)\\n\\n"
    if resume and hasattr(resume, 'model_dump_json'):
        # Use model_dump_json for direct JSON output with indentation
        resume_json = resume.model_dump_json(indent=2)
        markdown_content += f"```json\\n{resume_json}\\n```\\n\\n"
    else:
        markdown_content += "Resume not parsed or available.\\n\\n"

    markdown_content += "## Job Match Analysis (JSON)\\n\\n"
    if analysis and hasattr(analysis, 'model_dump_json'):
        analysis_json = analysis.model_dump_json(indent=2)
        markdown_content += f"```json\\n{analysis_json}\\n```\\n\\n"
    else:
        markdown_content += "Job Match Analysis not available (Job Description might be missing or analysis not run).\\n\\n"

    markdown_content += "## Hiring Decision & Rationale (JSON)\\n\\n"
    if decision and hasattr(decision, 'model_dump_json'):
        decision_json = decision.model_dump_json(indent=2)
        markdown_content += f"```json\\n{decision_json}\\n```\\n\\n"
    else:
        markdown_content += "Hiring Decision not available (Job Description might be missing or analysis not run).\\n\\n"

    return markdown_content

# --- Main App Content ---
def main():
    # Initialize session state
    initialize_session_state()
    
    # Apply dark theme
    st.markdown("""
    <style>
    .main {
        background-color: #121212;
        color: white;
    }
    .css-18ni7ap {
        background-color: #121212;
    }
    .css-1d391kg {
        background-color: #1E2F4D;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #1E2F4D;
        border-radius: 4px 4px 0 0;
        padding: 10px 16px;
        border: none;
        color: white;
    }
    .stTabs [aria-selected="true"] {
        background-color: #2E3F5D !important;
        border-bottom: 2px solid #1E90FF !important;
        color: white !important;
    }
    .main-header {
        background-color: #1E2F4D;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 20px;
        text-align: center;
    }
    .css-18e3th9 {
        padding-top: 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Page Header
    st.markdown(
        '<div class="main-header"><h1 style="color: white;">ATS Portal: Resume Analyzer & Job Matcher</h1></div>',
        unsafe_allow_html=True
    )
    
    # Create a single set of tabs for the entire application
    tabs = st.tabs(["Job Description", "Resume Scan", "Analysis", "Reports", "Resume Feedback"])
    
    # Content for the "Job Description" tab
    with tabs[0]:
        st.header("Job Description")
        job_desc_file = st.file_uploader("Option 1: Upload Job Description File", type=list(SUPPORTED_FILE_TYPES.values()))
        st.markdown("OR")
        job_desc_text_area = st.text_area("Option 2: Paste Job Description Text Here", height=200, value=st.session_state.job_description)
        
        if job_desc_text_area:
            st.session_state.job_description = job_desc_text_area
        
        if st.button("Save Job Description"):
            if job_desc_file or job_desc_text_area:
                st.success("Job description saved successfully!")
                st.session_state.active_tab = "Resume Scan"
            else:
                st.warning("Please provide a job description either by uploading a file or pasting text.")
    
    # Content for the "Resume Scan" tab
    with tabs[1]:
        st.header("Resume Scan")
        resume_file = st.file_uploader("Upload Resume", type=list(SUPPORTED_FILE_TYPES.values()))
        
        if resume_file and st.button("Process Resume"):
            process_resume(resume_file, job_desc_file, job_desc_text_area)
            st.session_state.active_tab = "Analysis"
    
    # Content for the "Analysis" tab
    with tabs[2]:
        if st.session_state.parsed_resume:
            create_analysis_dashboard(
                st.session_state.parsed_resume,
                st.session_state.match_analysis,
                st.session_state.decision
            )
        else:
            st.info("Upload and process a resume to see analysis here.")
    
    # Content for the "Reports" tab
    with tabs[3]:
        st.header("Candidate Screening Report")
        if st.session_state.parsed_resume:
            create_candidate_summary_page(
                st.session_state.parsed_resume,
                st.session_state.match_analysis,
                st.session_state.decision,
                st.session_state.job_description
            )

            # --- Download Button ---
            st.divider()
            st.subheader("Download Full Report")

            # Check if all necessary data is available for download
            report_ready = (
                st.session_state.parsed_resume and
                st.session_state.job_description and
                st.session_state.match_analysis and
                st.session_state.decision
            )

            if report_ready:
                markdown_report = create_download_markdown(
                    st.session_state.job_description,
                    st.session_state.parsed_resume,
                    st.session_state.match_analysis,
                    st.session_state.decision
                )
                # Generate a filename based on candidate name if possible
                try:
                    candidate_name = st.session_state.parsed_resume.contact_info.name.replace(" ", "_") or "candidate"
                except AttributeError:
                    candidate_name = "candidate"
                file_name = f"{candidate_name}_analysis_report.md"

                st.download_button(
                    label="Download Report as Markdown",
                    data=markdown_report,
                    file_name=file_name,
                    mime="text/markdown",
                )
            else:
                st.info("Process a resume and ensure a job description is provided to generate the full downloadable report.")
            # --- End Download Button ---

        else:
            st.info("Process a resume first to see candidate screening details and download the report here.")
    
    # Content for the "Resume Feedback" tab
    with tabs[4]:
        if st.session_state.parsed_resume:
            display_resume_with_feedback(
                st.session_state.parsed_resume,
                st.session_state.match_analysis
            )
        else:
            st.info("Process a resume first to see detailed feedback.")

# --- Processing Logic ---
def process_resume(resume_file_obj, job_desc_file_obj=None, job_desc_pasted_text=None):
    """
    Processes uploaded resume and optional job description (from file or text area).
    """
    if not resume_file_obj:
        st.warning("Please upload a resume file.")
        return

    # Check if API keys are available before proceeding
    if not MODELS['non_reasoning'].get('api_key') or not MODELS['reasoning'].get('api_key'):
         st.error("One or more API keys are missing. Cannot proceed with analysis.")
         return

    try:
        with st.spinner("Processing resume..."):
            # Initialize handlers
            file_handler = FileHandler()
            text_preprocessor = TextPreprocessor()

            # Save resume to temp file
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(resume_file_obj.name)[1]) as tmp_resume:
                tmp_resume.write(resume_file_obj.getvalue())
                resume_path = tmp_resume.name

            tmp_job_desc_path = None
            cleaned_job_desc = None

            # Process job description from file or text area
            if job_desc_file_obj:
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(job_desc_file_obj.name)[1]) as tmp_job:
                    tmp_job.write(job_desc_file_obj.getvalue())
                    tmp_job_desc_path = tmp_job.name
                st.info("Processing uploaded job description file.")
            elif job_desc_pasted_text:
                cleaned_job_desc = text_preprocessor.clean_text(job_desc_pasted_text)
                st.session_state.job_description = job_desc_pasted_text
                st.info("Processing pasted job description text.")

            # Extract and parse resume text
            resume_text = file_handler.extract_text(resume_path)
            cleaned_resume_text = text_preprocessor.clean_text(resume_text)

            # Parse resume
            resume_parser = ResumeParsingAgent(
                api_key=MODELS['non_reasoning']['api_key'],
                model_name=MODELS['non_reasoning']['name']
            )
            parsed_resume = resume_parser.parse_resume(cleaned_resume_text)
            if not isinstance(parsed_resume, ParsedResume):
                parsed_resume = ParsedResume(**parsed_resume)
            st.session_state.parsed_resume = parsed_resume

            # Process job matching if available
            job_desc_available = tmp_job_desc_path or cleaned_job_desc
            if job_desc_available:
                # Extract text from file if needed
                if tmp_job_desc_path:
                    job_desc_text = file_handler.extract_text(tmp_job_desc_path)
                    cleaned_job_desc = text_preprocessor.clean_text(job_desc_text)
                
                # Match job description against resume
                job_matcher = JobMatchingAgent(
                    api_key=MODELS['reasoning']['api_key'],
                    model_name=MODELS['reasoning']['name']
                )
                match_analysis = job_matcher.match_job(parsed_resume, cleaned_job_desc)
                if not isinstance(match_analysis, MatchAnalysis):
                    match_analysis = MatchAnalysis(**match_analysis)
                st.session_state.match_analysis = match_analysis

                # Generate hiring decision
                decision_agent = DecisionFeedbackAgent(
                    api_key=MODELS['reasoning']['api_key'],
                    model_name=MODELS['reasoning']['name']
                )
                decision = decision_agent.generate_decision(
                    candidate_profile=parsed_resume,
                    match_analysis=match_analysis,
                    job_requirements=cleaned_job_desc
                )
                if not isinstance(decision, DecisionFeedback):
                    decision = DecisionFeedback(**decision)
                st.session_state.decision = decision
                
                st.success("Resume processed and analyzed successfully!")
            else:
                st.warning("No job description provided. Only resume parsing completed.")
                st.session_state.match_analysis = MatchAnalysis()
                st.session_state.decision = DecisionFeedback()

    except Exception as e:
        st.error(f"An error occurred during processing: {str(e)}")
        import traceback
        st.error(traceback.format_exc())
        # Initialize empty models on error
        st.session_state.parsed_resume = ParsedResume()
        st.session_state.match_analysis = MatchAnalysis()
        st.session_state.decision = DecisionFeedback()

    finally:
        # Clean up temporary files
        if 'resume_path' in locals() and os.path.exists(resume_path):
            try:
                os.unlink(resume_path)
            except:
                pass
        if 'tmp_job_desc_path' in locals() and tmp_job_desc_path and os.path.exists(tmp_job_desc_path):
            try:
                os.unlink(tmp_job_desc_path)
            except:
                pass

# --- Sidebar Content ---
def add_sidebar():
    st.sidebar.header("Options")
    st.sidebar.markdown("---")
    
    st.sidebar.header("About")
    st.sidebar.info(
        """
        This ATS Portal allows you to:
        - Parse resumes into structured data
        - Match candidates against job requirements
        - Get detailed analysis and hiring recommendations
        - Visualize candidate metrics and scores
        """
    )
    
    st.sidebar.markdown("---")
    st.sidebar.header("Settings")
    
    # Add theme option (doesn't actually change the theme yet, just for UI purposes)
    theme = st.sidebar.selectbox(
        "Theme",
        ["Dark", "Light"],
        index=0
    )
    
    # Add sample data option
    if st.sidebar.button("Load Sample Data"):
        load_sample_data()
        st.sidebar.success("Sample data loaded!")

def load_sample_data():
    """Load sample data for demonstration"""
    try:
        with open('parsed_resume.json', 'r') as f:
            parsed_resume = json.load(f)
            st.session_state.parsed_resume = ParsedResume(**parsed_resume)
        
        # Create sample match analysis
        match_analysis = {
            "match_score": 72,
            "analysis": {
                "skills": {
                    "score": 85,
                    "matches": ["Python", "PyTorch", "TensorFlow", "Machine Learning"],
                    "gaps": ["Docker", "Kubernetes"]
                },
                "experience": {
                    "score": 65,
                    "matches": ["Research Experience", "Data Analysis"],
                    "gaps": ["Industry Experience", "Team Leadership"]
                },
                "education": {
                    "score": 90,
                    "matches": ["Computer Science Degree", "Data Science Focus"],
                    "gaps": []
                },
                "additional": {
                    "score": 60,
                    "matches": ["Project Documentation", "Technical Writing"],
                    "gaps": ["Certifications"]
                }
            },
            "recommendation": "The candidate shows strong technical skills in machine learning and data science, with excellent educational background. Consider proceeding with technical interviews to verify practical experience.",
            "key_strengths": [
                "Strong technical skills in ML/AI",
                "Excellent educational background",
                "Research experience"
            ],
            "areas_for_consideration": [
                "Limited industry experience",
                "Missing some DevOps skills",
                "Leadership experience unclear"
            ]
        }
        st.session_state.match_analysis = MatchAnalysis(**match_analysis)
        
        # Create sample decision
        decision = {
            "decision": {
                "status": "PROCEED",
                "confidence_score": 72,
                "interview_stage": "TECHNICAL"
            },
            "rationale": {
                "key_strengths": [
                    "Strong technical skills in machine learning and AI",
                    "Excellent academic background in relevant field",
                    "Demonstrated research experience"
                ],
                "concerns": [
                    "Limited industry experience",
                    "Some required skills missing",
                    "Leadership experience unclear"
                ],
                "risk_factors": [
                    "May need additional training on DevOps tools",
                    "Possible adjustment period for industry environment"
                ]
            },
            "recommendations": {
                "interview_focus": [
                    "Practical application of ML/AI skills",
                    "Problem-solving approach",
                    "Adaptability to industry workflows"
                ],
                "skill_verification": [
                    "Python coding proficiency",
                    "Understanding of ML frameworks",
                    "Data analysis skills"
                ],
                "discussion_points": [
                    "Interest in acquiring DevOps skills",
                    "Team collaboration experience",
                    "Learning goals and career aspirations"
                ]
            },
            "hiring_manager_notes": {
                "salary_band_fit": "Mid-level based on skills and experience",
                "growth_trajectory": "Strong potential for technical growth path",
                "team_fit_considerations": "Would benefit from mentoring by senior team members",
                "onboarding_requirements": [
                    "DevOps tools training",
                    "Industry best practices overview",
                    "Team workflow integration"
                ]
            },
            "next_steps": {
                "immediate_actions": [
                    "Schedule technical interview",
                    "Prepare coding assessment",
                    "Check references for research work"
                ],
                "required_approvals": [
                    "Hiring Manager approval for interview stage",
                    "Technical Team Lead review"
                ],
                "timeline_recommendation": "Proceed to technical interview within 1-2 weeks"
            }
        }
        st.session_state.decision = DecisionFeedback(**decision)
        
        # Sample job description
        st.session_state.job_description = """
        Machine Learning Research Engineer

        Job Description:
        We are seeking a talented Machine Learning Research Engineer with a strong background in deep learning and signal processing. The ideal candidate will work on cutting-edge research projects involving neural networks and process modeling.

        Required Skills:
        - Strong programming skills in Python
        - Experience with deep learning frameworks (PyTorch, TensorFlow)
        - Knowledge of signal processing and data analysis
        - Familiarity with research methodologies
        - Experience with version control (Git)

        Preferred Skills:
        - Experience with EEG data analysis
        - Knowledge of process mining
        - Familiarity with Docker
        - Experience with scientific writing and documentation
        - Background in statistical analysis

        Education:
        - Bachelor's or Master's degree in Computer Science, Data Science, or related field
        - Currently enrolled students with relevant research experience will be considered

        Responsibilities:
        - Develop and implement machine learning models
        - Conduct research experiments and document findings
        - Collaborate with cross-functional teams
        - Present research findings and technical documentation
        - Optimize existing models for better performance

        Experience:
        - Research experience in machine learning/deep learning
        - Previous internships in related fields
        - Demonstrated project work with neural networks
        """
    except Exception as e:
        st.error(f"Error loading sample data: {str(e)}")

# --- Initialization and Main Execution ---
if __name__ == "__main__":
    initialize_session_state()
    add_sidebar()
    main()