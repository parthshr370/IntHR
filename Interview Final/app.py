import streamlit as st
import os
from dotenv import load_dotenv

from agents.parser_agent import ParserAgent
from agents.interview_agent import InterviewAgent
from models.data_models import ParsedInput, InterviewGuide
from utils.log_config import logger

# Load environment variables
load_dotenv()

# Get API keys from environment
non_reasoning_api_key = os.getenv("NON_REASONING_API_KEY")
reasoning_api_key = os.getenv("REASONING_API_KEY")

# --- Streamlit App Layout ---
st.set_page_config(layout="wide")
st.title("AI Interview Guide Generator")

st.info("Paste the combined Job Description, Candidate Resume, and Online Assessment (OA) results below, OR upload a markdown file.")

# --- File Uploader and Text Input ---

# Initialize markdown_content in session state if it doesn't exist
if 'markdown_content' not in st.session_state:
    st.session_state.markdown_content = "" 

uploaded_file = st.file_uploader("Upload Markdown File (.md)", type=['md'])

# If a file is uploaded, read its content and update session state
if uploaded_file is not None:
    try:
        # Read file content as bytes, then decode
        bytes_data = uploaded_file.getvalue()
        st.session_state.markdown_content = bytes_data.decode("utf-8")
        logger.info(f"Uploaded file '{uploaded_file.name}' and read its content.")
    except Exception as e:
        st.error(f"Error reading file: {e}")
        logger.error(f"Error reading uploaded file '{uploaded_file.name}': {e}")
        # Reset to empty if error occurs
        st.session_state.markdown_content = ""

# Text area - now uses session state for its value
# Use a different key for the widget itself to avoid conflict if needed, 
# but linking its default value to session state is key.
st.text_area(
    "Paste Markdown Content Here (or see content from uploaded file):", 
    value=st.session_state.markdown_content, 
    height=400, 
    key="markdown_input_area" # Changed key to avoid potential conflicts
)

# Update session state if text area is changed manually
# This check ensures manual edits are captured if no file is uploaded
# or if the user modifies the text AFTER uploading.
if 'markdown_input_area' not in st.session_state:
    st.session_state.markdown_input_area = ""
if st.session_state.markdown_input_area != st.session_state.markdown_content:
    st.session_state.markdown_content = st.session_state.markdown_input_area

# Generate button
generate_button = st.button("Generate Interview Guide", key="generate_button")

# Placeholders for results
sidebar_placeholder = st.sidebar.empty()
tabs_placeholder = st.empty()

# --- Backend Logic --- 
# Use the content from session state for generation
if generate_button and st.session_state.markdown_content:
    if not non_reasoning_api_key or not reasoning_api_key:
        st.error("API keys not found. Please set NON_REASONING_API_KEY and REASONING_API_KEY in your .env file.")
    else:
        try:
            # 1. Initialize Agents
            parser_agent = ParserAgent(non_reasoning_api_key=non_reasoning_api_key)
            interview_agent = InterviewAgent(reasoning_api_key=reasoning_api_key)

            # 2. Parse Markdown
            with st.spinner("Parsing input markdown..."): 
                logger.info("Parsing markdown input...")
                # Use content from session state
                parsed_input: ParsedInput = parser_agent.parse_markdown(st.session_state.markdown_content)
                logger.info("Markdown parsing complete.")

            # 3. Display Parsed Data in Sidebar
            with sidebar_placeholder.container():
                st.header("Parsed Information")
                
                # Job Description Section
                with st.expander("📋 Job Description", expanded=True):
                    job_data = parsed_input.job_description.model_dump()
                    logger.info(f"Job Description data: {job_data}")
                    st.json(job_data)
                
                # Resume Data Section
                with st.expander("📄 Resume Data", expanded=True):
                    resume_data = parsed_input.resume_data.model_dump()
                    logger.info(f"Resume data: {resume_data}")
                    
                    # Display education
                    if resume_data.get('education'):
                        st.subheader('Education')
                        for edu in resume_data['education']:
                            st.markdown(f"**{edu.get('degree', 'Degree')}**")
                            st.markdown(f"*{edu.get('institution', 'Institution')}*")
                            st.markdown(f"_{edu.get('graduation_date', 'Date')}_")
                    
                    # Display experience
                    if resume_data.get('experience'):
                        st.subheader('Experience')
                        for exp in resume_data['experience']:
                            st.markdown(f"**{exp.get('title', 'Title')}**")
                            st.markdown(f"*{exp.get('company', 'Company')}* - {exp.get('location', '')}")
                            st.markdown(f"_{exp.get('start_date', '')} to {exp.get('end_date', '')}_")
                            if exp.get('responsibilities'):
                                st.markdown("Key Responsibilities:")
                                for resp in exp['responsibilities']:
                                    st.markdown(f"- {resp}")
                    
                    # Display projects
                    if resume_data.get('projects'):
                        st.subheader('Projects')
                        for proj in resume_data['projects']:
                            st.markdown(f"**{proj.get('name', 'Project')}**")
                            if proj.get('description'):
                                st.markdown(proj['description'])
                            if proj.get('technologies'):
                                st.markdown(f"*Technologies:* {', '.join(proj['technologies'])}")
                
                # OA Results Section
                with st.expander("📊 OA Results", expanded=True):
                    oa_data = parsed_input.oa_results.model_dump()
                    logger.info(f"OA Results data: {oa_data}")
                    st.subheader('Overall Results')
                    st.metric("Total Score", oa_data.get('total_score', 'N/A'))
                    st.metric("Status", oa_data.get('status', 'N/A'))
                    
                    if oa_data.get('performance_by_category'):
                        st.subheader('Performance by Category')
                        for category, score in oa_data['performance_by_category'].items():
                            st.metric(category, score)
                    
                    if oa_data.get('detailed_feedback'):
                        st.subheader('Detailed Feedback')
                        for area, feedback in oa_data['detailed_feedback'].items():
                            st.markdown(f"**{area}:**")
                            st.markdown(feedback)
                
                logger.info("Displayed parsed data in sidebar with formatting.")

            # 4. Generate Interview Guide
            with st.spinner("Generating interview questions... This may take a few minutes."): 
                logger.info("Generating interview guide...")
                interview_guide: InterviewGuide = interview_agent.generate_interview_guide(parsed_input)
                
                # Detailed logging of the interview guide structure
                logger.info("Interview guide generation complete. Details:")
                logger.info(f"Total sections: {len(interview_guide.sections)}")
                for section in interview_guide.sections:
                    logger.info(f"Section '{section.name}': {len(section.questions)} questions")
                    logger.info(f"First question in {section.name}: {section.questions[0].question if section.questions else 'No questions'}")

            # 5. Display Questions in Tabs
            with tabs_placeholder.container():
                st.empty()  # Clear any previous content
                st.header("Generated Interview Guide")
                
                # Create sections list for tabs
                sections = interview_guide.sections
                if not sections:
                    st.warning("No interview sections were generated.")
                    logger.warning("No sections found in interview guide.")
                    st.stop()
                
                # Create tabs with emojis for better visibility
                section_emojis = {
                    "Technical Assessment": "💻",  # 💻
                    "Coding Assessment": "⌨️",   # ⌨️
                    "Behavioral Assessment": "🗣",  # 🗣
                    "System Design": "🗜",       # 🗜
                }
                
                # Create tabs with emojis
                tab_names = [f"{section_emojis.get(section.name, '📄')} {section.name}" 
                            for section in sections]
                tabs = st.tabs(tab_names)
                
                # Display questions in each tab
                for tab, section in zip(tabs, sections):
                    with tab:
                        # Section header with metrics
                        col1, col2, col3 = st.columns([2, 1, 1])
                        with col1:
                            st.subheader(section.name)
                        with col2:
                            st.metric("Total Score", section.total_score)
                        with col3:
                            st.metric("Passing Score", section.passing_score)
                        
                        st.caption(section.description)
                        st.divider()
                        
                        # Questions
                        if not section.questions:
                            st.warning(f"No questions generated for {section.name}")
                            continue
                            
                        for idx, question in enumerate(section.questions, 1):
                            with st.expander(f"Q{idx}: {question.question[:100]}..."):
                                # Question details in columns for better organization
                                st.markdown("**Full Question:**")
                                st.write(question.question)
                                
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown(f"**Difficulty:** {'⭐' * question.difficulty} ({question.difficulty}/5)")
                                    st.markdown(f"**Score Value:** {question.score} points")
                                with col2:
                                    st.markdown(f"**Category:** {question.category}")
                                    st.markdown(f"**Question ID:** {question.id}")
                                
                                st.markdown("**Expected Answer:**")
                                st.info(question.expected_answer)
                                
                                st.markdown("**Rationale:**")
                                st.success(question.rationale)
                                
                                if question.follow_up_questions:
                                    st.markdown("**Follow-up Questions:**")
                                    for fq in question.follow_up_questions:
                                        st.markdown(f"- {fq}")
                
                # Display overall scores and notes
                st.divider()
                st.subheader("Overall Summary")
                st.markdown(f"**Total Guide Score:** {interview_guide.total_score}")
                st.markdown(f"**Overall Passing Score:** {interview_guide.passing_score}")
                
                if interview_guide.special_notes:
                    st.markdown("**Special Notes:**")
                    for note in interview_guide.special_notes:
                        st.markdown(f"- {note}")
                        
                if interview_guide.interviewer_guidelines:
                    st.markdown("**Interviewer Guidelines:**")
                    for guideline in interview_guide.interviewer_guidelines:
                        st.markdown(f"- {guideline}")
                        
                logger.info("Completed displaying interview guide in tabs.")

        except Exception as e:
            logger.error(f"An error occurred in the Streamlit app: {e}", exc_info=True)
            st.error(f"An error occurred: {e}")
            # Clear placeholders on error
            sidebar_placeholder.empty()
            tabs_placeholder.empty()
# Update condition to check session state
elif generate_button and not st.session_state.markdown_content:
    st.warning("Please paste the markdown content or upload a file first.")

# Initial state for placeholders
with sidebar_placeholder.container():
    st.header("Parsed Information")
    st.write("Results will appear here after generation.")

with tabs_placeholder.container():
    st.header("Generated Interview Guide")
    st.write("Questions will appear here after generation.")
