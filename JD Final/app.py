import streamlit as st
import json
import logging
import os
from dotenv import load_dotenv, set_key
from templates.form_template import STEP1_FIELDS, STEP2_FIELDS, STEP3_FIELDS, STEP4_FIELDS
from chains.workflow import run_workflow
from utils.validators import format_error_message
from config.settings import PREVIEW_MODE, JOB_PLATFORMS, LLM_PROVIDER
import markdown

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def create_step_form(step_fields):
    """Create a form from field definitions"""
    form_data = {}
    for field in step_fields:
        if field.get("type") == "text":
            form_data[field["key"]] = st.text_input(
                field["label"], 
                value=field.get("default", ""), 
                key=f"{field['key']}_input"
            )
        elif field.get("type") == "multiselect":
            form_data[field["key"]] = st.multiselect(
                field["label"], 
                options=field.get("options", []), 
                key=f"{field['key']}_input"
            )
        elif field.get("type") == "textarea":
            form_data[field["key"]] = st.text_area(
                field["label"], 
                key=f"{field['key']}_input"
            )
        elif field.get("type") == "select":
            form_data[field["key"]] = st.selectbox(
                field["label"], 
                options=field.get("options", []),
                index=0 if field.get("default") is None else field.get("options").index(field.get("default")),
                key=f"{field['key']}_input"
            )
    return form_data

def toggle_preview_mode(value):
    """Toggle preview mode in .env file"""
    try:
        # Update the environment variable in memory
        os.environ["PREVIEW_MODE"] = str(value)
        
        # Update the .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        set_key(env_path, "PREVIEW_MODE", str(value))
        
        # Force reload of settings module
        import importlib
        import config.settings
        importlib.reload(config.settings)
        
        return True
    except Exception as e:
        logger.error(f"Error toggling preview mode: {str(e)}")
        return False

def set_llm_provider(provider):
    """Set the LLM provider in .env file"""
    try:
        # Update the environment variable in memory
        os.environ["LLM_PROVIDER"] = provider
        
        # Update the .env file
        env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
        set_key(env_path, "LLM_PROVIDER", provider)
        
        # Force reload of settings module
        import importlib
        import config.settings
        importlib.reload(config.settings)
        
        return True
    except Exception as e:
        logger.error(f"Error setting LLM provider: {str(e)}")
        return False

def check_api_credentials(platform):
    """Check if required API credentials are set for a platform"""
    if platform == "twitter":
        return all([
            os.getenv("TWITTER_API_KEY"),
            os.getenv("TWITTER_API_SECRET"),
            os.getenv("TWITTER_ACCESS_TOKEN"),
            os.getenv("TWITTER_ACCESS_SECRET")
        ])
    elif platform == "google_jobs":
        return all([
            os.getenv("GOOGLE_JOBS_SERVICE_ACCOUNT_PATH"),
            os.getenv("GOOGLE_CLOUD_PROJECT_ID"),
            os.getenv("GOOGLE_JOBS_TENANT_ID"),
            os.getenv("GOOGLE_JOBS_COMPANY_ID")
        ])
    elif platform == "naukri":
        return bool(os.getenv("NAUKRI_API_KEY"))
    elif platform == "upwork":
        return all([
            os.getenv("UPWORK_API_KEY"),
            os.getenv("UPWORK_API_SECRET")
        ])
    return False

def check_llm_credentials(provider):
    """Check if required API credentials are set for the LLM provider"""
    if provider == "openai":
        return bool(os.getenv("OPENAI_API_KEY"))
    elif provider == "gemini":
        return bool(os.getenv("GEMINI_API_KEY"))
    return False

def render_job_description(job_description):
    """Render a job description with proper formatting"""
    # Split the content by sections to add custom styling
    sections = job_description.split('---')
    
    for section in sections:
        if not section.strip():
            continue
            
        # Render the section with proper markdown
        st.markdown(section.strip(), unsafe_allow_html=True)
        
        # Add a subtle divider between sections (except for the last one)
        if section != sections[-1]:
            st.markdown("<hr style='margin: 15px 0; opacity: 0.3;'>", unsafe_allow_html=True)

def main():
    st.set_page_config(
        page_title="Job Description Generator & Poster",
        page_icon="📝",
        layout="wide"
    )
    
    st.title("Job Description Generator & Poster")
    
    # Add a configuration sidebar
    with st.sidebar:
        st.header("Configuration")
        
        # LLM Provider selection
        st.subheader("AI Provider")
        current_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        
        provider_options = ["gemini", "openai"]
        selected_provider = st.selectbox(
            "Select AI Provider", 
            options=provider_options,
            index=provider_options.index(current_provider),
            key="llm_provider"
        )
        
        # Check if provider credentials are set
        provider_credentials_ok = check_llm_credentials(selected_provider)
        
        if selected_provider != current_provider:
            if set_llm_provider(selected_provider):
                st.success(f"AI Provider changed to {selected_provider.capitalize()}")
            else:
                st.error(f"Failed to change AI Provider")
        
        if not provider_credentials_ok:
            st.warning(f"⚠️ {selected_provider.capitalize()} API key not set. Please add it to your .env file.")
        
        # Get current preview mode status
        current_preview_mode = os.getenv("PREVIEW_MODE", "True").lower() == "true"
        
        # Preview mode toggle
        st.subheader("Posting Mode")
        preview_mode = st.toggle(
            "Preview Mode", 
            value=current_preview_mode,
            help="When enabled, jobs won't be actually posted to platforms"
        )
        
        # Update preview mode if changed
        if preview_mode != current_preview_mode:
            if toggle_preview_mode(preview_mode):
                st.success(f"Preview mode {'enabled' if preview_mode else 'disabled'}")
            else:
                st.error("Failed to update preview mode")
        
        # Platform configuration
        st.subheader("Platform Status")
        
        for platform, config in JOB_PLATFORMS.items():
            enabled = config["enabled"]
            credentials_ok = check_api_credentials(platform)
            
            status = "✅ Ready" if enabled and credentials_ok else "⚠️ Not Configured"
            if enabled and not credentials_ok:
                status = "❌ Missing Credentials"
            
            st.write(f"{platform.capitalize()}: {status}")
        
        # API Keys configuration link
        with st.expander("API Keys Configuration"):
            st.write("You need to set API keys in your .env file for each platform.")
            st.write("Check the README.md for instructions.")
    
    st.write("Fill in the details below to generate a professional job description and publish to job platforms.")
    
    # Show AI provider info
    st.info(f"**Using {selected_provider.capitalize()} AI** to generate job descriptions")
    
    if preview_mode:
        st.info("**PREVIEW MODE ENABLED**: Jobs will not be actually posted to platforms.")
    else:
        st.warning("**LIVE MODE ENABLED**: Jobs will be posted to enabled platforms.")
    
    # Initialize session state
    if 'current_step' not in st.session_state:
        st.session_state.current_step = 1
    
    if 'job_input' not in st.session_state:
        st.session_state.job_input = {}
    
    if 'job_description' not in st.session_state:
        st.session_state.job_description = ""
    
    if 'posting_results' not in st.session_state:
        st.session_state.posting_results = {}
    
    if 'errors' not in st.session_state:
        st.session_state.errors = []
    
    # Process navigation buttons
    if st.session_state.current_step == 5:  # Result page
        if st.button("Start Over"):
            st.session_state.current_step = 1
            st.session_state.job_input = {}
            st.session_state.job_description = ""
            st.session_state.posting_results = {}
            st.session_state.errors = []
            st.rerun()
    
    # Multi-step form
    if st.session_state.current_step == 1:
        st.header("Step 1: Company Culture & Values")
        st.write("Let's build the foundation! Your culture, your values, your perfect match.")
        
        step1_data = create_step_form(STEP1_FIELDS)
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col2:
            if st.button("Next"):
                # Save data and advance
                st.session_state.job_input.update(step1_data)
                st.session_state.current_step = 2
                st.rerun()
    
    elif st.session_state.current_step == 2:
        st.header("Step 2: Manager's Requirements/Insights")
        st.write("Customizing for your team's unique needs.")
        
        step2_data = create_step_form(STEP2_FIELDS)
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Previous"):
                st.session_state.current_step = 1
                st.rerun()
        with col2:
            if st.button("Next"):
                # Save data and advance
                st.session_state.job_input.update(step2_data)
                st.session_state.current_step = 3
                st.rerun()
    
    elif st.session_state.current_step == 3:
        st.header("Step 3: Industry-Standards and Customization")
        st.write("Time to tap into industry standards! We've got you covered.")
        
        step3_data = create_step_form(STEP3_FIELDS)
        
        # Navigation buttons
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("Previous"):
                st.session_state.current_step = 2
                st.rerun()
        with col2:
            if st.button("Next"):
                # Save data and advance
                st.session_state.job_input.update(step3_data)
                st.session_state.current_step = 4
                st.rerun()
    
    elif st.session_state.current_step == 4:
        st.header("Step 4: Job-Specific Customization")
        st.write("Final touch – Tailoring for the perfect role fit!")
        
        step4_data = create_step_form(STEP4_FIELDS)
        
        # Navigation buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("Previous"):
                st.session_state.current_step = 3
                st.rerun()
        with col3:
            generate_label = f"Generate with {selected_provider.capitalize()}"
            button_text = f"{generate_label} & {'Preview' if preview_mode else 'Post'}"
            
            if st.button(button_text):
                # Check if API key is set
                if not check_llm_credentials(selected_provider):
                    st.error(f"{selected_provider.capitalize()} API key not set. Please add it to your .env file.")
                else:
                    # Save data and process
                    st.session_state.job_input.update(step4_data)
                    
                    # Run the workflow
                    with st.spinner(f"Processing your job description using {selected_provider.capitalize()} AI..."):
                        try:
                            # Pass the preview_mode flag to the workflow
                            result = run_workflow(st.session_state.job_input)
                            
                            # Save results
                            st.session_state.job_description = result.get("job_description", "")
                            st.session_state.posting_results = result.get("posting_results", {})
                            st.session_state.errors = result.get("errors", [])
                            
                            # Advance to result page
                            st.session_state.current_step = 5
                            st.rerun()
                        except Exception as e:
                            st.error(f"An unexpected error occurred: {str(e)}")
                            logger.exception("Error during workflow execution")
    
    elif st.session_state.current_step == 5:
        st.header("Results")
        
        if st.session_state.errors:
            st.error(format_error_message(st.session_state.errors))
            st.button("Fix Errors", on_click=lambda: setattr(st.session_state, 'current_step', 1))
        else:
            st.success(f"Job description generated successfully using {LLM_PROVIDER.capitalize()} AI" + 
                      (" (Preview Mode)" if preview_mode else ""))
            
            # Display the job description with enhanced formatting
            st.subheader("Generated Job Description")
            
            # Use custom rendering for better formatting
            with st.container():
                render_job_description(st.session_state.job_description)
            
            # Display posting results
            if preview_mode:
                st.subheader("Job Posting Previews")
            else:
                st.subheader("Job Posting Results")
            
            if st.session_state.posting_results:
                for platform, result in st.session_state.posting_results.items():
                    if result.get("success"):
                        st.success(f"{platform.capitalize()}: {result.get('message')}")
                    else:
                        st.warning(f"{platform.capitalize()}: {result.get('message')}")
            else:
                st.info("No posting results available")
            
            # Export options
            st.subheader("Export Options")
            
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download as Markdown",
                    data=st.session_state.job_description,
                    file_name="job_description.md",
                    mime="text/markdown"
                )
            
            with col2:
                # Convert markdown to HTML for HTML download
                try:
                    html_content = f"""
                    <!DOCTYPE html>
                    <html>
                    <head>
                        <meta charset="utf-8">
                        <title>Job Description</title>
                        <style>
                            body {{ font-family: Arial, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 20px; }}
                            h1 {{ color: #2c3e50; }}
                            h2 {{ color: #3498db; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                            hr {{ border: 0; height: 1px; background: #eee; margin: 20px 0; }}
                            ul {{ padding-left: 20px; }}
                            li {{ margin-bottom: 8px; }}
                        </style>
                    </head>
                    <body>
                        {markdown.markdown(st.session_state.job_description)}
                    </body>
                    </html>
                    """
                    
                    st.download_button(
                        label="Download as HTML",
                        data=html_content,
                        file_name="job_description.html",
                        mime="text/html"
                    )
                except Exception as e:
                    st.error(f"Error generating HTML: {str(e)}")
            
            # Start over button
            st.button("Create Another Job Description", on_click=lambda: setattr(st.session_state, 'current_step', 1))

if __name__ == "__main__":
    main()