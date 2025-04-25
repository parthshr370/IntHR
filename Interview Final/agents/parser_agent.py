import logging
import json
from pydantic import SecretStr, ValidationError
from langchain_openai import ChatOpenAI
from models.data_models import ParsedInput, JobDescription, ResumeData, OAResult
from templates.prompts import PARSE_INPUT_PROMPT
from typing import Optional

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.info("Initializing ParserAgent")

class ParserAgent:
    """Agent for parsing markdown input containing JD, resume, and OA results"""
    
    def __init__(self, non_reasoning_api_key: str):
        """Initialize parser agent with API key"""
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            temperature=0.2,
            openai_api_key=non_reasoning_api_key,
            openai_api_base="https://openrouter.ai/api/v1",
            max_tokens=4096
        )
        
    @staticmethod
    def _parse_rating_string(rating_str: Optional[str]) -> float:
        """Parse a 'score/max_score' string into a float score/max_score."""
        if not isinstance(rating_str, str):
            return 0.0
        try:
            parts = rating_str.split('/')
            if len(parts) == 2:
                score = float(parts[0].strip())
                max_score = float(parts[1].strip())
                if max_score != 0:
                    # Return the calculated ratio
                    return score / max_score 
                else:
                    return 0.0 # Avoid division by zero
            else:
                # If format is unexpected, try converting directly
                return float(rating_str.strip()) 
        except (ValueError, TypeError, IndexError):
            logger.warning(f"Could not parse rating string: '{rating_str}'. Defaulting to 0.0.")
            return 0.0

    def parse_markdown(self, markdown_content: str) -> ParsedInput:
        """Parse markdown content to extract structured data using LLM."""
        try:
            # Step 1: Raw text is now the input markdown_content itself (No longer call extract_raw_text)
            raw_text = markdown_content 

            # Step 2: Invoke LLM with the raw markdown content
            prompt = PARSE_INPUT_PROMPT.format(content=raw_text)
            result = self.llm.invoke(prompt)
            
            # Step 3: Let the LLM handle the parsing and structuring
            parsed_text = result.content
            
            # Clean up potential markdown code blocks
            if "```json" in parsed_text:
                parsed_text = parsed_text.split("```json", 1)[1]
            if "```" in parsed_text:
                parsed_text = parsed_text.split("```", 1)[0]
            
            # Parse JSON
            try:
                llm_output = json.loads(parsed_text.strip())
                logger.debug(f"Raw LLM Output Dictionary: {llm_output}")
                
                # Create Pydantic models
                job_description = JobDescription(
                    job_title=llm_output.get("job_description", {}).get("job_title", "Software Engineer"),
                    location=llm_output.get("job_description", {}).get("location", "Remote"),
                    experience_level=llm_output.get("job_description", {}).get("experience_level", "Mid-level"),
                    responsibilities=llm_output.get("job_description", {}).get("responsibilities", ["Development"]),
                    qualifications=llm_output.get("job_description", {}).get("qualifications", ["Programming"]),
                    preferred_qualifications=llm_output.get("job_description", {}).get("preferred_qualifications", [])
                )
                
                resume_data = ResumeData(
                    personal_info=llm_output.get("resume_data", {}).get("personal_info", {"name": "Candidate"}),
                    summary=llm_output.get("resume_data", {}).get("summary", ""),
                    education=llm_output.get("resume_data", {}).get("education", []),
                    experience=llm_output.get("resume_data", {}).get("experience", []),
                    skills=llm_output.get("resume_data", {}).get("skills", ["Programming"]),
                    projects=llm_output.get("resume_data", {}).get("projects", []),
                    certifications=llm_output.get("resume_data", {}).get("certifications", [])
                )
                
                # Preprocess OA Results ratings
                oa_data = llm_output.get("oa_results", {})
                tech_rating_str = oa_data.get("technical_rating")
                passion_rating_str = oa_data.get("passion_rating")
                perf_by_cat_raw = oa_data.get("performance_by_category", {})
                total_score_str = oa_data.get("total_score") # Get the raw total score
                
                # Parse total_score string (e.g., '29/100' -> 29)
                parsed_total_score = 0
                if isinstance(total_score_str, str):
                    try:
                        score_part = total_score_str.split('/')[0]
                        parsed_total_score = int(float(score_part.strip())) # Use float first for potential decimals like '80.0/100'
                    except (ValueError, TypeError, IndexError):
                        logger.warning(f"Could not parse total_score string: '{total_score_str}'. Defaulting to 0.")
                elif isinstance(total_score_str, (int, float)):
                     parsed_total_score = int(total_score_str)

                perf_by_cat_processed = {
                    category: self._parse_rating_string(score_str)
                    for category, score_str in perf_by_cat_raw.items()
                }

                oa_results = OAResult(
                    total_score=parsed_total_score, # Use the parsed integer score
                    status=oa_data.get("status", "UNKNOWN"),
                    technical_rating=self._parse_rating_string(tech_rating_str),
                    passion_rating=self._parse_rating_string(passion_rating_str),
                    performance_by_category=perf_by_cat_processed,
                    detailed_feedback=oa_data.get("detailed_feedback", {})
                )
                
                return ParsedInput(
                    job_description=job_description,
                    resume_data=resume_data,
                    oa_results=oa_results
                )
                
            except json.JSONDecodeError as e:
                logger.error(f"JSON parsing error: {e}")
                logger.error(f"Raw text received: {parsed_text[:500]}...")
                raise
                
        except Exception as e:
            logger.error(f"Error in parse_markdown: {e}")
            raise 