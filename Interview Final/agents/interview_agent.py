import logging
import json
import uuid
from typing import List, Dict, Any
from datetime import datetime

from langchain_openai import ChatOpenAI
from models.data_models import (
    ParsedInput, InterviewQuestion, InterviewSection, 
    InterviewGuide
)
from templates.prompts import (
    TECHNICAL_QUESTION_PROMPT, BEHAVIORAL_QUESTION_PROMPT,
    SYSTEM_DESIGN_PROMPT, CODING_QUESTION_PROMPT
)

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.info("Initializing InterviewAgent")

class InterviewAgent:
    """Agent for generating interview questions and guides"""
    
    def __init__(self, reasoning_api_key: str):
        """Initialize interview agent with API key"""
        self.llm = ChatOpenAI(
            model="google/gemini-2.5-pro-preview-03-25",
            temperature=0.7,
            openai_api_key=reasoning_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=4096
        )
        
    def generate_interview_guide(self, parsed_input: ParsedInput) -> InterviewGuide:
        """Generate a complete interview guide (Synchronous)"""
        logger.info("Starting synchronous interview guide generation...")
        try:
            # Generate questions for each section synchronously
            sections = []
            
            # Technical questions
            logger.info("Generating technical questions...")
            technical_questions = self._generate_technical_questions(parsed_input)
            if technical_questions:
                logger.info(f"Generated {len(technical_questions)} technical questions.")
                sections.append(InterviewSection(
                    name="Technical Assessment",
                    description="Core technical knowledge and problem-solving evaluation",
                    questions=technical_questions,
                    total_score=sum(q.score for q in technical_questions),
                    passing_score=int(sum(q.score for q in technical_questions) * 0.7)
                ))
            
            # Coding questions
            logger.info("Generating coding questions...")
            coding_questions = self._generate_coding_questions(parsed_input)
            if coding_questions:
                logger.info(f"Generated {len(coding_questions)} coding questions.")
                sections.append(InterviewSection(
                    name="Coding Challenge",
                    description="Live coding and algorithm implementation",
                    questions=coding_questions,
                    total_score=sum(q.score for q in coding_questions),
                    passing_score=int(sum(q.score for q in coding_questions) * 0.7)
                ))
            
            # System design questions (for mid/senior levels)
            if parsed_input.job_description.experience_level.lower() in ["mid", "senior"]:
                logger.info("Generating system design questions...")
                design_questions = self._generate_system_design_questions(parsed_input)
                if design_questions:
                    logger.info(f"Generated {len(design_questions)} system design questions.")
                    sections.append(InterviewSection(
                        name="System Design",
                        description="Architecture and scalability discussion",
                        questions=design_questions,
                        total_score=sum(q.score for q in design_questions),
                        passing_score=int(sum(q.score for q in design_questions) * 0.7)
                    ))
            
            # Behavioral questions
            logger.info("Generating behavioral questions...")
            behavioral_questions = self._generate_behavioral_questions(parsed_input)
            if behavioral_questions:
                logger.info(f"Generated {len(behavioral_questions)} behavioral questions.")
                sections.append(InterviewSection(
                    name="Behavioral Assessment",
                    description="Soft skills and cultural fit evaluation",
                    questions=behavioral_questions,
                    total_score=sum(q.score for q in behavioral_questions),
                    passing_score=int(sum(q.score for q in behavioral_questions) * 0.7)
                ))
            
            logger.info("Successfully generated all question sections.")
            # Calculate totals
            total_score = sum(section.total_score for section in sections)
            passing_score = sum(section.passing_score for section in sections)
            
            # Generate final guide
            guide = InterviewGuide(
                candidate_name=parsed_input.resume_data.personal_info.name,
                job_title=parsed_input.job_description.job_title,
                interview_date=datetime.now(),
                sections=sections,
                total_score=total_score,
                passing_score=passing_score,
                special_notes=[
                    f"Candidate's OA Score: {parsed_input.oa_results.total_score}",
                    f"Technical Rating: {parsed_input.oa_results.technical_rating}",
                    f"Areas of Focus: {', '.join(parsed_input.oa_results.performance_by_category.keys())}"
                ],
                interviewer_guidelines=[
                    "Review OA results before interview",
                    "Focus on areas where candidate showed weakness in OA",
                    "Validate strong areas from OA with practical questions",
                    "Allow time for candidate questions at the end"
                ]
            )
            
            logger.info("Successfully created InterviewGuide object.")
            return guide
            
        except Exception as e:
            logger.error(f"Error generating interview guide: {e}", exc_info=True)
            # Return a minimal guide or re-raise, depending on desired behavior
            return InterviewGuide( # Return minimal guide on error
                 candidate_name=parsed_input.resume_data.personal_info.name if parsed_input.resume_data else "N/A",
                 job_title=parsed_input.job_description.job_title if parsed_input.job_description else "N/A",
                 interview_date=datetime.now().isoformat(),
                 sections=[],
                 total_score=0,
                 passing_score=0,
                 special_notes=["Error occurred during generation"],
                 interviewer_guidelines=[]
             )
        
    def _generate_technical_questions(self, parsed_input: ParsedInput) -> List[InterviewQuestion]:
        """Generate technical interview questions (Synchronous)"""
        logger.info("Attempting synchronous technical question LLM call...")
        try:
            # Use synchronous invoke
            result = self.llm.invoke(TECHNICAL_QUESTION_PROMPT.format(
                job_description=parsed_input.job_description.model_dump(),
                resume=parsed_input.resume_data.model_dump(),
                oa_results=parsed_input.oa_results.model_dump()
            ))
            
            logger.info("Successfully received response for technical questions.")
            questions_data = self._parse_questions_response(result.content)
            if not questions_data:
                 logger.warning("Parsing technical questions response yielded no data.")
                 return []
            return [
                InterviewQuestion(
                    id=f"tech_{uuid.uuid4().hex[:8]}",
                    **q
                ) for q in questions_data
            ]
            
        except Exception as e:
            logger.error(f"Error generating technical questions: {e}", exc_info=True)
            return []
            
    def _generate_behavioral_questions(self, parsed_input: ParsedInput) -> List[InterviewQuestion]:
        """Generate behavioral interview questions (Synchronous)"""
        logger.info("Attempting synchronous behavioral question LLM call...")
        try:
            # Use synchronous invoke
            result = self.llm.invoke(BEHAVIORAL_QUESTION_PROMPT.format(
                job_description=parsed_input.job_description.model_dump(),
                resume=parsed_input.resume_data.model_dump(),
                oa_results=parsed_input.oa_results.model_dump()
            ))
            
            logger.info("Successfully received response for behavioral questions.")
            questions_data = self._parse_questions_response(result.content)
            if not questions_data:
                 logger.warning("Parsing behavioral questions response yielded no data.")
                 return []
            return [
                InterviewQuestion(
                    id=f"behavior_{uuid.uuid4().hex[:8]}",
                    **q
                ) for q in questions_data
            ]
            
        except Exception as e:
            logger.error(f"Error generating behavioral questions: {e}", exc_info=True)
            return []
            
    def _generate_system_design_questions(self, parsed_input: ParsedInput) -> List[InterviewQuestion]:
        """Generate system design interview questions (Synchronous)"""
        logger.info("Attempting synchronous system design question LLM call...")
        try:
            # Use synchronous invoke
            result = self.llm.invoke(SYSTEM_DESIGN_PROMPT.format(
                job_description=parsed_input.job_description.model_dump(),
                resume=parsed_input.resume_data.model_dump(),
                oa_results=parsed_input.oa_results.model_dump(),
                level=parsed_input.job_description.experience_level
            ))
            
            logger.info("Successfully received response for system design questions.")
            questions_data = self._parse_questions_response(result.content)
            if not questions_data:
                 logger.warning("Parsing system design questions response yielded no data.")
                 return []
            return [
                InterviewQuestion(
                    id=f"design_{uuid.uuid4().hex[:8]}",
                    **q
                ) for q in questions_data
            ]
            
        except Exception as e:
            logger.error(f"Error generating system design questions: {e}", exc_info=True)
            return []
            
    def _generate_coding_questions(self, parsed_input: ParsedInput) -> List[InterviewQuestion]:
        """Generate coding interview questions (Synchronous)"""
        logger.info("Attempting synchronous coding question LLM call...")
        try:
            # Use synchronous invoke
            result = self.llm.invoke(CODING_QUESTION_PROMPT.format(
                job_description=parsed_input.job_description.model_dump(),
                resume=parsed_input.resume_data.model_dump(),
                oa_results=parsed_input.oa_results.model_dump(),
                level=parsed_input.job_description.experience_level
            ))
            
            logger.info("Successfully received response for coding questions.")
            questions_data = self._parse_questions_response(result.content)
            if not questions_data:
                 logger.warning("Parsing coding questions response yielded no data.")
                 return []
            return [
                InterviewQuestion(
                    id=f"code_{uuid.uuid4().hex[:8]}",
                    **q
                ) for q in questions_data
            ]
            
        except Exception as e:
            logger.error(f"Error generating coding questions: {e}", exc_info=True)
            return []
            
    def _parse_questions_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into question dictionaries"""
        # Log the raw response before attempting to parse
        logger.info(f"--- Raw LLM question response start ---\n{response}\n--- Raw LLM question response end ---")
        try:
            # Clean up markdown formatting
            if "```json" in response:
                response = response.split("```json", 1)[1]
            if "```" in response:
                response = response.split("```", 1)[0]
                
            data = json.loads(response.strip())
            
            # Handle different response formats
            if isinstance(data, list):
                return data
            elif isinstance(data, dict) and "questions" in data:
                return data["questions"]
            else:
                return [data]
                
        except Exception as e:
            logger.error(f"Error parsing questions response: {e}")
            return [] 