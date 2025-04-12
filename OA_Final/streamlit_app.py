import streamlit as st
import asyncio
import json
import logging
from datetime import datetime
from main import OAModule
import os
from pathlib import Path
from dotenv import load_dotenv
from config import API_CONFIG, NON_REASONING_MODEL, REASONING_MODEL

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.info("Initializing streamlit_app.py")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

class StreamlitApp:
    def __init__(self):
        """Initialize Streamlit app with OA module"""
        # Initialize session state variables
        self._init_session_state()
        
        # Check environment setup
        if not self._verify_environment():
            st.error("""
            Environment setup error. Please ensure:
            1. Your .env file exists in the project root
            2. The file contains NON_REASONING_API_KEY and REASONING_API_KEY
            3. The values are correct and not empty
            
            Required formats:
            - NON_REASONING_API_KEY should start with 'sk-or-'
            - REASONING_API_KEY should start with 'sk-'
            """)
            st.stop()
            
        # Initialize OA Module
        try:
            if not st.session_state.oa_module:
                logger.info("Initializing OA Module...")
                st.session_state.oa_module = OAModule()
                logger.info("OA Module initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing OA Module: {str(e)}")
            st.error(f"Error initializing OA Module: {str(e)}")
            st.stop()

    def _init_session_state(self):
        """Initialize all session state variables"""
        if 'oa_module' not in st.session_state:
            st.session_state.oa_module = None
        if 'assessment' not in st.session_state:
            st.session_state.assessment = None
        if 'responses' not in st.session_state:
            st.session_state.responses = {}
        if 'result' not in st.session_state:
            st.session_state.result = None
        if 'parsing_error' not in st.session_state:
            st.session_state.parsing_error = None
        if 'markdown_content' not in st.session_state:
            st.session_state.markdown_content = None
        logger.info("Session state initialized")

    def _verify_environment(self) -> bool:
        """Verify environment setup with detailed logging"""
        env_paths = ['.env', '../.env', Path(__file__).parent / '.env', Path(__file__).parent.parent / '.env']
        
        # Log environment path checking
        env_found = False
        for env_path in env_paths:
            logger.info(f"Checking for .env at: {env_path}")
            if Path(env_path).exists():
                logger.info(f"Found .env file at: {env_path}")
                load_dotenv(env_path)
                env_found = True
                break
                
        if not env_found:
            logger.warning("No .env file found in any of the expected locations")
        
        # Check and log API keys (safely)
        non_reasoning_key = os.getenv("NON_REASONING_API_KEY")
        reasoning_key = os.getenv("REASONING_API_KEY")
        
        logger.info(f"NON_REASONING_API_KEY exists: {bool(non_reasoning_key)}")
        if non_reasoning_key:
            logger.info(f"NON_REASONING_API_KEY prefix: {non_reasoning_key[:10]}...")
            if not non_reasoning_key.startswith('sk-or-'):
                logger.error("NON_REASONING_API_KEY has incorrect format")
                return False
            
        logger.info(f"REASONING_API_KEY exists: {bool(reasoning_key)}")
        if reasoning_key:
            logger.info(f"REASONING_API_KEY prefix: {reasoning_key[:10]}...")
            if not reasoning_key.startswith('sk-'):
                logger.error("REASONING_API_KEY has incorrect format")
                return False
        
        # Log API configuration
        logger.info(f"API Config: {json.dumps(API_CONFIG, indent=2)}")
        logger.info(f"Model Config - NON_REASONING_MODEL: {NON_REASONING_MODEL}")
        logger.info(f"Model Config - REASONING_MODEL: {REASONING_MODEL}")
        
        if not non_reasoning_key or not reasoning_key:
            logger.warning("Failed to load API keys from .env, checking environment variables...")
            non_reasoning_key = os.environ.get("NON_REASONING_API_KEY")
            reasoning_key = os.environ.get("REASONING_API_KEY")
        
        return bool(non_reasoning_key and reasoning_key)

    async def process_markdown(self, markdown_content: str):
        """Process markdown and generate assessment"""
        if not markdown_content:
            st.error("Markdown content is empty.")
            return

        # Store the original markdown content
        st.session_state.markdown_content = markdown_content

        try:
            logger.info("Processing markdown content...")
            st.session_state.parsing_error = None
            
            # First analyze the content
            analysis = await st.session_state.oa_module.analyzer.analyze_content(markdown_content)
            logger.info(f"Content analysis completed: {json.dumps(analysis, indent=2)}")
            
            # Generate assessment
            assessment = await st.session_state.oa_module.process_input(markdown_content)
            st.session_state.assessment = assessment
            st.session_state.responses = {}
            
            logger.info("Assessment generated successfully")
            return True
            
        except Exception as e:
            error_msg = f"Error processing markdown: {str(e)}"
            logger.error(error_msg)
            st.session_state.parsing_error = error_msg
            return False

    def render_question(self, question, question_type: str):
        """Render a single question with response input"""
        try:
            st.subheader(f"{question_type} Question")
            st.write(question.text)
            
            if question_type == "Coding":
                # Process options to remove the "Option X: " prefix if present
                display_options = []
                for option in question.options:
                    if option.startswith("Option ") and ":" in option:
                        # Format: "Option A: content" -> extract just "content"
                        # But keep the letter as a prefix for readability
                        letter = option[7:8]  # Extract A, B, C, or D
                        content = option.split(":", 1)[1].strip()
                        display_options.append(f"{letter}. {content}")
                    else:
                        display_options.append(option)
                        
                # Use the processed options for display
                response = st.radio(
                    f"Select answer for Question {question.id}",
                    display_options,
                    key=f"radio_{question.id}"
                )
                
                # Map the selection back to the original index
                selected_index = display_options.index(response)
                st.session_state.responses[question.id] = selected_index
                
            elif question_type == "System Design":
                st.write("Scenario:", question.scenario)
                st.write("Expected Components:", ", ".join(question.expected_components))
                response = st.text_area(
                    "Your solution",
                    key=f"design_{question.id}",
                    height=200
                )
                st.session_state.responses[question.id] = response
                
            else:  # Behavioral
                st.write("Context:", question.context)
                response = st.text_area(
                    "Your response",
                    key=f"behavioral_{question.id}",
                    height=150
                )
                st.session_state.responses[question.id] = response
                
            logger.debug(f"Question {question.id} rendered successfully")
            
        except Exception as e:
            logger.error(f"Error rendering question {question.id}: {str(e)}")
            st.error(f"Error rendering question: {str(e)}")

    async def evaluate_responses(self):
        """Evaluate all responses"""
        try:
            logger.info("Starting response evaluation...")
            result = await st.session_state.oa_module.evaluate_responses(
                st.session_state.assessment,
                st.session_state.responses
            )
            st.session_state.result = result
            logger.info("Response evaluation completed successfully")
            return True
        except Exception as e:
            logger.error(f"Error evaluating responses: {str(e)}")
            st.error(f"Error evaluating responses: {str(e)}")
            return False

    def render_results(self):
        """Render assessment results"""
        try:
            if not st.session_state.result:
                logger.warning("No results to render")
                return

            result = st.session_state.result
            st.title("Assessment Results")
            
            # Overall score
            score_color = "green" if result.passed else "red"
            col1, col2 = st.columns([2, 1])
            with col1:
                st.progress(result.score / 100)
            with col2:
                st.markdown(f"<h2 style='color: {score_color}'>{result.score:.1f}%</h2>", unsafe_allow_html=True)
            
            st.write(f"Status: {'PASSED ' if result.passed else 'FAILED '}")
            
            # Ratings
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Technical Rating", f"{result.technical_rating:.2f}/1.0")
                st.progress(result.technical_rating)
            with col2:
                st.metric("Passion Rating", f"{result.passion_rating:.2f}/1.0")
                st.progress(result.passion_rating)
            
            # Detailed feedback
            st.header("Detailed Feedback")
            for question_id, feedback in result.feedback.items():
                score = result.question_scores[question_id]
                with st.expander(f"Question {question_id} - Score: {score}/100"):
                    st.write(feedback)
                    st.progress(score / 100)

            # Generate detailed report
            detailed_report = st.session_state.oa_module.generate_report(result)
            
            # Extract scores by category from question_scores
            coding_scores = []
            design_scores = []
            behavioral_scores = []
            
            for qid, score in result.question_scores.items():
                if qid.startswith("code_"):
                    coding_scores.append(score)
                elif qid.startswith("design_"):
                    design_scores.append(score)
                elif qid.startswith("behavior_"):
                    behavioral_scores.append(score)
            
            # Download buttons
            st.header("Download Options")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                result_json = json.dumps(
                    st.session_state.result.dict(),
                    indent=2,
                    cls=DateTimeEncoder
                )
                st.download_button(
                    " Download Results (JSON)",
                    result_json,
                    "assessment_results.json",
                    "application/json"
                )
            
            with col2:
                assessment_json = json.dumps(
                    st.session_state.assessment.dict(),
                    indent=2,
                    cls=DateTimeEncoder
                )
                st.download_button(
                    " Download Assessment",
                    assessment_json,
                    "assessment.json",
                    "application/json"
                )
                
            with col3:
                st.download_button(
                    " Download Detailed Report",
                    detailed_report,
                    "assessment_report.txt",
                    "text/plain"
                )
            
            # Add the combined Markdown download button below the columns
            if st.session_state.markdown_content:
                combined_content = f"# Original Input\n\n{st.session_state.markdown_content}\n\n<hr>\n\n# Assessment Report\n\n{detailed_report}"
                file_name = f"assessment_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                st.download_button(
                    label=" Download Combined Report (Markdown)",
                    data=combined_content,
                    file_name=file_name,
                    mime='text/markdown'
                )
            
            # Display report preview
            st.header(" Assessment Summary Report")

            # Filter tabs based on content availability
            tabs_to_display = ["Overview"] # Start with Overview
            if "CODING QUESTIONS" in detailed_report:
                tabs_to_display.append("Coding")
            if "SYSTEM DESIGN QUESTIONS" in detailed_report:
                tabs_to_display.append("System Design")
            if "BEHAVIORAL QUESTIONS" in detailed_report:
                tabs_to_display.append("Behavioral")
            if "SUMMARY & RECOMMENDATIONS" in detailed_report:
                tabs_to_display.append("Summary & Recs")

            # Extract sections more robustly
            sections = []
            current_section_content = []
            for line in detailed_report.split('\n'):
                if line.strip() and line.startswith("====="):
                    if current_section_content:
                        sections.append(current_section_content)
                        current_section_content = []
                else:
                    current_section_content.append(line)
            if current_section_content:
                sections.append(current_section_content)

            # Create tabs ONLY for sections with content
            report_tabs = st.tabs(tabs_to_display)

            # Map tab titles to their actual index in report_tabs
            tab_map = {title: i for i, title in enumerate(tabs_to_display)}

            # Overview Tab
            with report_tabs[tab_map["Overview"]]:
                # Extract and highlight the overview section
                overview_section = '\n'.join(sections[0])
                
                # Highlight the overall score
                score_color = "green" if result.passed else "red"
                overview_lines = overview_section.split('\n')
                formatted_overview = []
                
                for line in overview_lines:
                    if line.startswith("Total Score:"):
                        score_value = line.split(":")[1].strip()
                        formatted_overview.append(f"**Total Score:** <span style='color:{score_color};font-weight:bold;'>{score_value}</span>")
                    elif line.startswith("Status:"):
                        status = "PASSED " if result.passed else "FAILED "
                        formatted_overview.append(f"**Status:** <span style='color:{score_color};font-weight:bold;'>{status}</span>")
                    elif line.startswith("Technical Rating:") or line.startswith("Passion Rating:"):
                        parts = line.split(":")
                        formatted_overview.append(f"**{parts[0]}:** **{parts[1].strip()}**")
                    elif line.startswith("Strongest Area:") or line.startswith("Needs Improvement:"):
                        parts = line.split(":")
                        formatted_overview.append(f"**{parts[0]}:** *{parts[1].strip()}*")
                    elif "PERFORMANCE BY CATEGORY" in line:
                        formatted_overview.append(f"### {line}")
                    elif "OVERALL RESULTS" in line:
                        formatted_overview.append(f"## {line}")
                    elif line.strip() and len(line.strip()) > 3:  # Skip empty or separator lines
                        formatted_overview.append(line)
                
                st.markdown('\n'.join(formatted_overview), unsafe_allow_html=True)
                
                # Add score visualization
                st.markdown("#### Score Distribution")
                score_data = {
                    "Category": ["Coding", "System Design", "Behavioral"],
                    "Score": [
                        sum(coding_scores) / len(coding_scores) if coding_scores else 0,
                        sum(design_scores) / len(design_scores) if design_scores else 0,
                        sum(behavioral_scores) / len(behavioral_scores) if behavioral_scores else 0
                    ]
                }
                
                # Display visual bar chart of scores
                for i, category in enumerate(score_data["Category"]):
                    st.markdown(f"**{category}**")
                    st.progress(score_data["Score"][i] / 100)
                    st.markdown(f"{score_data['Score'][i]:.1f}/100")

            # Coding Questions Tab
            if "Coding" in tab_map:
                coding_section = '\n'.join([line for section in sections for line in section if "CODING QUESTIONS" in line])
                
                with report_tabs[tab_map["Coding"]]:
                    st.markdown("## Coding Questions")
                    
                    # Extract strengths and improvements
                    if "Coding Strengths:" in coding_section:
                        strengths = coding_section.split("Coding Strengths:")[1].split("Coding Areas for Improvement:")[0]
                        st.markdown("### Strengths")
                        for line in strengths.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                    
                    if "Coding Areas for Improvement:" in coding_section:
                        improvements = coding_section.split("Coding Areas for Improvement:")[1]
                        st.markdown("### Areas for Improvement")
                        for line in improvements.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                                
                    # Format individual questions
                    st.markdown("### Question Details")
                    question_blocks = [q for q in coding_section.split("\nQuestion ID:") if q.strip()]
                    for i, block in enumerate(question_blocks):
                        if i == 0 and not block.startswith("Question ID:"):
                            # Skip the header
                            continue
                        
                        lines = ["Question ID:" + block.strip() if i > 0 else block.strip()]
                        q_id = lines[0].split("Question ID:")[1].split("\n")[0].strip() if "Question ID:" in lines[0] else "Unknown"
                        score_line = [l for l in lines[0].split("\n") if "Score:" in l][0] if [l for l in lines[0].split("\n") if "Score:" in l] else "Score: 0/100"
                        score = int(score_line.split("Score:")[1].split("/")[0].strip())
                        
                        st.markdown(f"**Question {q_id} - Score: {score}/100**")
                        st.progress(score / 100)
                        st.markdown(lines[0].replace("Question ID:", "**Question ID:**").replace("Score:", "**Score:**").replace("Feedback:", "**Feedback:**"))
                        st.divider()

            # System Design Tab
            if "System Design" in tab_map:
                design_section = '\n'.join([line for section in sections for line in section if "SYSTEM DESIGN QUESTIONS" in line])
                
                with report_tabs[tab_map["System Design"]]:
                    st.markdown("## System Design Questions")
                    
                    # Extract strengths and improvements
                    if "System Design Strengths:" in design_section:
                        strengths = design_section.split("System Design Strengths:")[1].split("System Design Areas for Improvement:")[0]
                        st.markdown("### Strengths")
                        for line in strengths.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                    
                    if "System Design Areas for Improvement:" in design_section:
                        improvements = design_section.split("System Design Areas for Improvement:")[1]
                        st.markdown("### Areas for Improvement")
                        for line in improvements.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                                
                    # Format individual questions
                    st.markdown("### Question Details")
                    question_blocks = [q for q in design_section.split("\nQuestion ID:") if q.strip()]
                    for i, block in enumerate(question_blocks):
                        if i == 0 and not block.startswith("Question ID:"):
                            # Skip the header
                            continue
                        
                        lines = ["Question ID:" + block.strip() if i > 0 else block.strip()]
                        q_id = lines[0].split("Question ID:")[1].split("\n")[0].strip() if "Question ID:" in lines[0] else "Unknown"
                        score_line = [l for l in lines[0].split("\n") if "Score:" in l][0] if [l for l in lines[0].split("\n") if "Score:" in l] else "Score: 0/100"
                        score = int(score_line.split("Score:")[1].split("/")[0].strip())
                        
                        st.markdown(f"**Question {q_id} - Score: {score}/100**")
                        st.progress(score / 100)
                        st.markdown(lines[0].replace("Question ID:", "**Question ID:**").replace("Score:", "**Score:**").replace("Feedback:", "**Feedback:**"))
                        st.divider()

            # Behavioral Questions Tab
            if "Behavioral" in tab_map:
                behavioral_section = '\n'.join([line for section in sections for line in section if "BEHAVIORAL QUESTIONS" in line])
                
                with report_tabs[tab_map["Behavioral"]]:
                    st.markdown("## Behavioral Questions")
                    
                    # Extract strengths and improvements
                    if "Behavioral Strengths:" in behavioral_section:
                        strengths = behavioral_section.split("Behavioral Strengths:")[1].split("Behavioral Areas for Improvement:")[0]
                        st.markdown("### Strengths")
                        for line in strengths.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                    
                    if "Behavioral Areas for Improvement:" in behavioral_section:
                        improvements = behavioral_section.split("Behavioral Areas for Improvement:")[1]
                        st.markdown("### Areas for Improvement")
                        for line in improvements.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                                
                    # Format individual questions
                    st.markdown("### Question Details")
                    question_blocks = [q for q in behavioral_section.split("\nQuestion ID:") if q.strip()]
                    for i, block in enumerate(question_blocks):
                        if i == 0 and not block.startswith("Question ID:"):
                            # Skip the header
                            continue
                        
                        lines = ["Question ID:" + block.strip() if i > 0 else block.strip()]
                        q_id = lines[0].split("Question ID:")[1].split("\n")[0].strip() if "Question ID:" in lines[0] else "Unknown"
                        score_line = [l for l in lines[0].split("\n") if "Score:" in l][0] if [l for l in lines[0].split("\n") if "Score:" in l] else "Score: 0/100"
                        score = int(score_line.split("Score:")[1].split("/")[0].strip())
                        
                        st.markdown(f"**Question {q_id} - Score: {score}/100**")
                        st.progress(score / 100)
                        st.markdown(lines[0].replace("Question ID:", "**Question ID:**").replace("Score:", "**Score:**").replace("Feedback:", "**Feedback:**"))
                        st.divider()

            # Recommendations Tab
            if "Summary & Recs" in tab_map:
                recommendations_section = '\n'.join([line for section in sections for line in section if "SUMMARY & RECOMMENDATIONS" in line])
                
                with report_tabs[tab_map["Summary & Recs"]]:
                    st.markdown("## Summary & Recommendations")
                    
                    # Format the recommendations
                    # Key Strengths
                    if "Key Strengths:" in recommendations_section:
                        strengths = recommendations_section.split("Key Strengths:")[1].split("Areas for Improvement:")[0]
                        st.markdown("### Key Strengths")
                        for line in strengths.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                    
                    # Areas for Improvement
                    if "Areas for Improvement:" in recommendations_section:
                        improvements = recommendations_section.split("Areas for Improvement:")[1].split("Recommendations:")[0]
                        st.markdown("### Areas for Improvement")
                        for line in improvements.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                    
                    # Recommendations
                    if "Recommendations:" in recommendations_section:
                        recommendations = recommendations_section.split("Recommendations:")[1]
                        st.markdown("### Recommendations")
                        for line in recommendations.strip().split('\n'):
                            if line.strip().startswith('-'):
                                st.markdown(f" {line.strip()[2:]}")
                                
                        # Add final advice based on passing status
                        if result.passed:
                            st.success("**OVERALL RECOMMENDATION:** This candidate has demonstrated the necessary skills and should be considered for the next stage of the interview process.")
                        else:
                            st.warning("**OVERALL RECOMMENDATION:** This candidate may need additional preparation or may not be the best fit for this specific role at this time.")

            # Option to view raw report text
            st.expander("View Raw Report Text", expanded=False).text(detailed_report)
            
            logger.info("Results rendered successfully")
            
        except Exception as e:
            logger.error(f"Error rendering results: {str(e)}")
            st.error(f"Error rendering results: {str(e)}")

    def render_header(self):
        """Render the header of the app"""
        st.title(" HR Portal - Online Assessment")
        st.write("""
        Welcome to the online assessment platform. This tool helps generate and evaluate 
        technical assessments based on job descriptions and candidate profiles.
        """)

    def render_sidebar(self):
        """Render the sidebar with additional information"""
        st.sidebar.title("About")
        st.sidebar.info("""
        This tool uses AI to:
        - Analyze job descriptions and resumes
        - Generate tailored questions
        - Evaluate responses
        - Provide detailed feedback
        """)
        
        st.sidebar.title("Instructions")
        st.sidebar.info("""
        1. Upload your markdown file or enter content directly
        2. Generate the assessment
        3. Answer the questions
        4. Submit for evaluation
        """)

    def run(self):
        """Main app execution"""
        try:
            self.render_header()
            self.render_sidebar()
            
            # File upload section
            st.subheader(" Input Data")
            upload_method = st.radio(
                "Choose input method",
                ["Upload File", "Enter Text"],
                help="Select how you want to provide the JD and resume data"
            )
            
            markdown_content = ""
            
            if upload_method == "Upload File":
                uploaded_file = st.file_uploader(
                    "Upload markdown file (JD + Resume)",
                    type=['md', 'txt'],
                    help="File should contain job description and resume in markdown format"
                )
                if uploaded_file:
                    markdown_content = uploaded_file.read().decode()
                    
            else:  # Enter Text
                markdown_content = st.text_area(
                    "Enter markdown content",
                    height=300,
                    help="Paste or type the job description and resume in markdown format"
                )
            
            # Preview and analysis section
            if markdown_content:
                with st.expander(" Preview Raw Content", expanded=False):
                    st.code(markdown_content, language="markdown")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(" Preview Analysis", type="secondary"):
                        with st.spinner("Analyzing content..."):
                            analysis = asyncio.run(
                                st.session_state.oa_module.analyzer.analyze_content(markdown_content)
                            )
                            st.json(analysis)
                
                with col2:
                    if st.button(" Generate Assessment", type="primary"):
                        with st.spinner("Generating assessment..."):
                            success = asyncio.run(self.process_markdown(markdown_content))
                            
                            if not success and st.session_state.parsing_error:
                                st.error("Failed to generate assessment")
                                with st.expander("Error Details"):
                                    st.code(st.session_state.parsing_error)
            
            # Render assessment if available
            if st.session_state.assessment:
                assessment = st.session_state.assessment
                
                st.header(" Online Assessment")
                st.write(f"Candidate: {assessment.candidate_name}")
                st.write(f"Position: {assessment.job_title}")
                
                # Questions sections
                question_tabs = st.tabs([
                    " Coding Questions", 
                    " System Design Questions", 
                    " Behavioral Questions"
                ])
                
                with question_tabs[0]:
                    coding_questions = assessment.coding_questions
                    if coding_questions:
                        # Add pagination for coding questions
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col2:
                            coding_page = st.selectbox(
                                "Navigate Coding Questions", 
                                options=range(1, len(coding_questions) + 1),
                                format_func=lambda x: f"Question {x} of {len(coding_questions)}",
                                key="coding_pagination"
                            )
                        st.divider()
                        # Display the selected question (0-indexed)
                        self.render_question(coding_questions[coding_page - 1], "Coding")
                        
                with question_tabs[1]:
                    design_questions = assessment.system_design_questions
                    if design_questions:
                        # Add pagination for system design questions
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col2:
                            design_page = st.selectbox(
                                "Navigate System Design Questions", 
                                options=range(1, len(design_questions) + 1),
                                format_func=lambda x: f"Question {x} of {len(design_questions)}",
                                key="design_pagination"
                            )
                        st.divider()
                        # Display the selected question (0-indexed)
                        self.render_question(design_questions[design_page - 1], "System Design")
                        
                with question_tabs[2]:
                    behavioral_questions = assessment.behavioral_questions
                    if behavioral_questions:
                        # Add pagination for behavioral questions
                        col1, col2, col3 = st.columns([1, 3, 1])
                        with col2:
                            behavioral_page = st.selectbox(
                                "Navigate Behavioral Questions", 
                                options=range(1, len(behavioral_questions) + 1),
                                format_func=lambda x: f"Question {x} of {len(behavioral_questions)}",
                                key="behavioral_pagination"
                            )
                        st.divider()
                        # Display the selected question (0-indexed)
                        self.render_question(behavioral_questions[behavioral_page - 1], "Behavioral")
                
                # Submit section
                st.subheader(" Submit Assessment")
                col1, col2 = st.columns(2)
                with col1:
                    st.info(f"Total questions: {len(assessment.coding_questions) + len(assessment.system_design_questions) + len(assessment.behavioral_questions)}")
                    st.progress(len(st.session_state.responses) / (len(assessment.coding_questions) + len(assessment.system_design_questions) + len(assessment.behavioral_questions)))
                    st.write(f"Questions answered: {len(st.session_state.responses)}")
                
                with col2:
                    if st.button("Submit Responses", type="primary", disabled=len(st.session_state.responses) == 0):
                        with st.spinner("Evaluating responses..."):
                            if asyncio.run(self.evaluate_responses()):
                                self.render_results()
                            
        except Exception as e:
            logger.error(f"Error in main app execution: {str(e)}")
            st.error(f"An error occurred: {str(e)}")

def main():
    st.set_page_config(
        page_title="HR Portal - Online Assessment",
        page_icon="",
        layout="wide",
        initial_sidebar_state="expanded"
    )
    
    try:
        logger.info("Starting HR Portal application...")
        app = StreamlitApp()
        app.run()
        logger.info("Application running successfully")
    except Exception as e:
        logger.error(f"Critical application error: {str(e)}")
        st.error("""
        Critical application error. Please ensure:
        1. Your .env file is properly configured
        2. API keys are valid
        3. All dependencies are installed
        
        Error details:
        """
        + str(e))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {str(e)}")
        st.error("An unexpected error occurred. Please check the logs for details.")