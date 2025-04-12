# agents/assessment_agent.py

import os
import logging # Add logging import
import re # Import re for cleaning JSON
from typing import Dict, Any, List, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import json
from models.data_models import Assessment, AssessmentResult  # noqa: E402
from config import REASONING_MODEL, API_CONFIG, ASSESSMENT_CONFIG
from datetime import datetime

# Configure logger for this module
logger = logging.getLogger(__name__)


class AssessmentAgent:
    """Agent for evaluating candidate responses and generating feedback"""
    
    def __init__(self, reasoning_api_key: str):
        """Initialize with OpenAI API key for reasoning tasks"""
        self.llm = ChatOpenAI(
            model=REASONING_MODEL,
            temperature=0.1,
            openai_api_key=reasoning_api_key,
            base_url="https://openrouter.ai/api/v1",
            openai_api_base=API_CONFIG["reasoning"]["base_url"]
        )
        
        self._init_prompts()
        
    def _init_prompts(self):
        """Initialize evaluation prompts for different question types"""
        self.coding_eval_prompt = PromptTemplate(
            input_variables=["question", "candidate_answer", "correct_answer", "level"],
            template="""
            Evaluate this coding question response for a {level}-level candidate:
            
            Question: {question}
            Candidate's Answer (option selected): {candidate_answer}
            Correct Answer: {correct_answer}
            
            Provide evaluation in JSON format:
            {{
                "score": int,  # 0-100
                "technical_accuracy": float,  # 0-1
                "code_quality": float,  # 0-1
                "problem_solving": float,  # 0-1
                "feedback": str,
                "strengths": list[str],
                "improvement_areas": list[str]
            }}
            """
        )
        
        self.system_design_eval_prompt = PromptTemplate(
            input_variables=["scenario", "candidate_solution", "requirements", "level", "score"],
            template="""
            Evaluate this system design solution for a {level}-level candidate:
            
            Scenario: {scenario}
            Requirements: {requirements}
            Candidate's Solution: {candidate_solution}
            Maximum Score: {score}
            
            Provide evaluation in JSON format:
            {{
                "score": int,  # 0-100
                "architecture_quality": float,  # 0-1
                "scalability_consideration": float,  # 0-1
                "security_consideration": float,  # 0-1
                "feedback": str,
                "strengths": list[str],
                "weaknesses": list[str],
                "recommendations": list[str]
            }}
            """
        )
        
        self.behavioral_eval_prompt = PromptTemplate(
            input_variables=["question", "response", "criteria", "level", "score"],
            template="""
            Evaluate this behavioral response for a {level}-level candidate:
            
            Question: {question}
            Response: {response}
            Evaluation Criteria: {criteria}
            Maximum Score: {score}
            
            Provide evaluation in JSON format:
            {{
                "score": int,  # 0-100
                "communication": float,  # 0-1
                "experience_relevance": float,  # 0-1
                "problem_solving": float,  # 0-1
                "leadership": float,  # 0-1
                "passion_indicators": list[str],
                "feedback": str,
                "strengths": list[str],
                "areas_for_growth": list[str]
            }}
            """
        )

    @staticmethod
    def _extract_json(text: str) -> Optional[Dict[str, Any]]:
        """Extracts the first valid JSON object from a string using multiple strategies."""
        if not text:
            return None
            
        # Strategy 1: Look for JSON object pattern
        match = re.search(r'{\s*".*?"\s*:.*?}', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                return json.loads(json_str)
            except json.JSONDecodeError:
                pass  # Try next strategy
        
        # Strategy 2: Extract content from markdown code blocks
        code_block_match = re.search(r'```(?:json)?(.*?)```', text, re.DOTALL)
        if code_block_match:
            code_content = code_block_match.group(1).strip()
            try:
                return json.loads(code_content)
            except json.JSONDecodeError:
                pass  # Try next strategy
        
        # Strategy 3: Find the largest text between curly braces
        curly_matches = list(re.finditer(r'{.*?}', text, re.DOTALL))
        if curly_matches:
            # Sort by length of match, longest first (most likely to be the complete JSON)
            sorted_matches = sorted(curly_matches, key=lambda m: len(m.group(0)), reverse=True)
            for match in sorted_matches:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    continue  # Try next match
        
        # Strategy 4: Try to fix common JSON errors and extract again
        # Remove any leading/trailing text
        fixed_text = re.sub(r'^[^{]*', '', text)  # Remove anything before first {
        fixed_text = re.sub(r'[^}]*$', '', fixed_text)  # Remove anything after last }
        
        # Fix common quote issues (single vs double quotes)
        fixed_text = fixed_text.replace("'", '"')
        
        # Try to parse the fixed text
        try:
            return json.loads(fixed_text)
        except json.JSONDecodeError:
            pass  # All strategies failed
            
        # If all approaches fail, try a more aggressive approach to at least extract key-value pairs
        try:
            # Extract what looks like key-value pairs
            kv_pairs = re.findall(r'"([^"]+)"\s*:\s*([^,\}]+)', text)
            if kv_pairs:
                result = {}
                for k, v in kv_pairs:
                    # Try to convert value to appropriate type
                    v = v.strip().rstrip(',')
                    if v.lower() == 'true':
                        result[k] = True
                    elif v.lower() == 'false':
                        result[k] = False
                    elif v.lower() == 'null':
                        result[k] = None
                    elif re.match(r'^".*"$', v):  # String
                        result[k] = v.strip('"')
                    elif re.match(r'^-?\d+\.\d+$', v):  # Float
                        result[k] = float(v)
                    elif re.match(r'^-?\d+$', v):  # Integer
                        result[k] = int(v)
                    else:
                        result[k] = v  # Keep as string
                return result
        except Exception:
            pass
            
        logger.warning("No JSON object could be extracted from LLM response.")
        return None
            
    async def evaluate_answer(
        self,
        question_type: str,
        question_data: Dict[str, Any],
        candidate_answer: str,
        level: str
    ) -> Dict[str, Any]:
        """Evaluate a single answer based on question type, with robust JSON parsing."""
        logger.info(f"Evaluating {question_type} answer for level {level}. Question ID: {question_data.get('id', 'N/A')}")
        logger.debug(f"Question data received: {question_data}") # Log question data
        
        try:
            if question_type == "coding":
                # Use direct reasoning approach
                return await self._evaluate_coding_by_reasoning(question_data, candidate_answer, level)
                
            elif question_type == "system_design":
                # Use direct reasoning approach
                return await self._evaluate_system_design_by_reasoning(question_data, candidate_answer, level)
                
            elif question_type == "behavioral":
                # Use direct reasoning approach
                return await self._evaluate_behavioral_by_reasoning(question_data, candidate_answer, level)
                
            else:
                logger.error(f"Unsupported question type encountered: {question_type}")
                raise ValueError(f"Unsupported question type: {question_type}")
            
        except KeyError as ke:
             # Specific handling for missing keys in question_data
             logger.error(f"Missing key in question_data during evaluation prompt formatting: {ke}", exc_info=True)
             logger.error(f"Problematic question_data: {question_data}")
             return {"score": 0, "feedback": f"Error: Configuration issue - missing data for evaluation ({ke}).", "strengths": [], "improvement_areas": ["Configuration Error"]}
        except Exception as e:
            # General error handling
            logger.error(f"Error evaluating {question_type} answer ID {question_data.get('id')}: {str(e)}", exc_info=True)
            return {
                "score": 0, 
                "feedback": f"Error evaluating answer: {str(e)}",
                "strengths": [],
                "improvement_areas": ["Evaluation Error"]
            }

    async def _evaluate_coding_by_reasoning(
        self, 
        question_data: Dict[str, Any], 
        candidate_answer: str, 
        level: str
    ) -> Dict[str, Any]:
        """
        Evaluate coding questions using direct reasoning without needing a correct_answer key.
        This uses the question, options, and explanation to evaluate the candidate's response.
        """
        try:
            # Get the question text and options
            question_text = question_data.get("text", "")
            options = question_data.get("options", [])
            
            # Get the candidate's answer (could be index or text)
            answer_text = None
            answer_index = None
            
            if isinstance(candidate_answer, int) or candidate_answer.isdigit():
                # If candidate_answer is an index
                answer_index = int(candidate_answer)
                if 0 <= answer_index < len(options):
                    answer_text = options[answer_index]
                else:
                    answer_text = f"Invalid option index: {answer_index}"
            else:
                # If candidate_answer is text, find the matching option
                answer_text = candidate_answer
                for i, option in enumerate(options):
                    if option.lower() == candidate_answer.lower():
                        answer_index = i
                        break
            
            # Get the explanation from the question data, if available
            explanation = question_data.get("explanation", "")
            max_score = question_data.get("score", 10)
            
            # Create the evaluation prompt
            eval_prompt = f"""
            You are evaluating a candidate's answer to a coding question. Use direct reasoning to evaluate the answer.
            
            Question: {question_text}
            
            Options:
            {', '.join([f"{i}. {opt}" for i, opt in enumerate(options)])}
            
            Candidate's answer: {answer_text}
            
            Additional context (explanation): {explanation}
            
            Evaluate whether the candidate's answer is correct and provide a JSON response with:
            1. A score from 0 to {max_score} (where {max_score} is the maximum)
            2. Technical accuracy rating (0.0 to 1.0)
            3. Problem-solving assessment (0.0 to 1.0)
            4. Feedback explaining the evaluation
            5. Strengths demonstrated in the answer
            6. Areas for improvement
            
            Return only a JSON object:
            {{
                "score": int,
                "technical_accuracy": float,
                "problem_solving": float,
                "feedback": "Your detailed feedback here",
                "strengths": ["Strength 1", "Strength 2"],
                "improvement_areas": ["Area 1", "Area 2"]
            }}
            """
            
            # Send to the LLM for evaluation
            logger.debug(f"Sending direct reasoning prompt for evaluation:\n{eval_prompt}")
            llm_response = await self.llm.ainvoke(eval_prompt)
            raw_content = llm_response.content
            
            # Extract and parse JSON
            parsed_json = self._extract_json(raw_content)
            
            if parsed_json:
                 logger.info(f"Successfully parsed direct reasoning evaluation for question ID {question_data.get('id')}")
                 
                 # Check if we need to normalize the score to 0-100 scale
                 if "score" in parsed_json and parsed_json["score"] < 100:
                     # If the score is less than 100, assume it's on the max_score scale
                     if parsed_json["score"] > max_score:
                         # Cap at max_score if needed
                         parsed_json["score"] = max_score
                     
                     # Convert to 0-100 scale
                     parsed_json["score"] = int((parsed_json["score"] / max_score) * 100)
                 
                 return parsed_json
            else:
                 logger.error(f"Could not parse JSON from direct reasoning evaluation. Raw content was:\n{raw_content}")
                 return {
                     "score": 0,
                     "technical_accuracy": 0.0,
                     "problem_solving": 0.0,
                     "feedback": "Error: Could not parse evaluation response.",
                     "strengths": [],
                     "improvement_areas": ["Evaluation Error"]
                 }
            
        except Exception as e:
            logger.error(f"Error in direct reasoning evaluation: {str(e)}", exc_info=True)
            return {
                "score": 0,
                "technical_accuracy": 0.0,
                "problem_solving": 0.0,
                "feedback": f"Error evaluating answer: {str(e)}",
                "strengths": [],
                "improvement_areas": ["Evaluation Error"]
            }

    async def _evaluate_system_design_by_reasoning(
        self, 
        question_data: Dict[str, Any], 
        candidate_answer: str, 
        level: str
    ) -> Dict[str, Any]:
        """
        Evaluate system design questions using direct reasoning.
        This uses the scenario, requirements, and evaluation criteria to assess the candidate's solution.
        """
        try:
            # Get the question data
            scenario = question_data.get("scenario", "")
            requirements = question_data.get("requirements", [])
            expected_components = question_data.get("expected_components", [])
            evaluation_criteria = question_data.get("evaluation_criteria", [])
            max_score = question_data.get("score", 10)
            
            # Create a comprehensive evaluation prompt
            eval_prompt = f"""
            You are evaluating a candidate's solution to a system design question for a {level}-level position.
            
            System Design Scenario: {scenario}
            
            Requirements:
            {', '.join([f"- {req}" for req in requirements])}
            
            Expected Components:
            {', '.join([f"- {comp}" for comp in expected_components])}
            
            Evaluation Criteria:
            {', '.join([f"- {crit}" for crit in evaluation_criteria])}
            
            Candidate's Solution:
            {candidate_answer}
            
            Evaluate the candidate's solution comprehensively and provide a JSON response with:
            1. A score from 0 to {max_score} (where {max_score} is the maximum)
            2. Architecture quality rating (0.0 to 1.0)
            3. Scalability consideration rating (0.0 to 1.0)
            4. Security consideration rating (0.0 to 1.0)
            5. Detailed feedback explaining the evaluation
            6. Strengths demonstrated in the solution
            7. Weaknesses or areas that need improvement
            8. Recommendations for improvement
            
            Return only a JSON object:
            {{
                "score": int,
                "architecture_quality": float,
                "scalability_consideration": float,
                "security_consideration": float,
                "feedback": "Your detailed feedback here",
                "strengths": ["Strength 1", "Strength 2"],
                "weaknesses": ["Weakness 1", "Weakness 2"],
                "recommendations": ["Recommendation 1", "Recommendation 2"]
            }}
            """
            
            # Send to the LLM for evaluation
            logger.debug(f"Sending system design reasoning prompt for evaluation:\n{eval_prompt}")
            llm_response = await self.llm.ainvoke(eval_prompt)
            raw_content = llm_response.content
            
            # Extract and parse JSON
            parsed_json = self._extract_json(raw_content)
            
            if parsed_json:
                 logger.info(f"Successfully parsed system design evaluation for question ID {question_data.get('id')}")
                 
                 # Normalize the score to 0-100 scale if needed
                 if "score" in parsed_json and parsed_json["score"] < 100:
                     # If the score is less than 100, assume it's on the max_score scale
                     if parsed_json["score"] > max_score:
                         # Cap at max_score if needed
                         parsed_json["score"] = max_score
                     
                     # Convert to 0-100 scale
                     parsed_json["score"] = int((parsed_json["score"] / max_score) * 100)
                 
                 return parsed_json
            else:
                 logger.error(f"Could not parse JSON from system design evaluation. Raw content was:\n{raw_content}")
                 return {
                     "score": 0,
                     "architecture_quality": 0.0,
                     "scalability_consideration": 0.0,
                     "security_consideration": 0.0,
                     "feedback": "Error: Could not parse evaluation response.",
                     "strengths": [],
                     "weaknesses": [],
                     "recommendations": []
                 }
            
        except Exception as e:
            logger.error(f"Error in system design evaluation: {str(e)}", exc_info=True)
            return {
                "score": 0,
                "architecture_quality": 0.0,
                "scalability_consideration": 0.0,
                "security_consideration": 0.0,
                "feedback": f"Error evaluating answer: {str(e)}",
                "strengths": [],
                "weaknesses": [],
                "recommendations": []
            }
    
    async def _evaluate_behavioral_by_reasoning(
        self, 
        question_data: Dict[str, Any], 
        candidate_answer: str, 
        level: str
    ) -> Dict[str, Any]:
        """
        Evaluate behavioral questions using direct reasoning.
        This uses the question context, evaluation points, and cultural fit markers to assess the response.
        """
        try:
            # Get the question data
            question_text = question_data.get("text", "")
            context = question_data.get("context", "")
            evaluation_points = question_data.get("evaluation_points", [])
            passion_indicators = question_data.get("passion_indicators", [])
            cultural_fit_markers = question_data.get("cultural_fit_markers", [])
            max_score = question_data.get("score", 10)
            
            # Check if candidate_answer is empty or None
            if not candidate_answer or candidate_answer.strip() == "":
                logger.warning(f"Empty response for behavioral question ID {question_data.get('id')}")
                return {
                    "score": 0,
                    "communication": 0.0,
                    "experience_relevance": 0.0,
                    "problem_solving": 0.0,
                    "leadership": 0.0,
                    "passion_indicators": [],
                    "feedback": "No response provided.",
                    "strengths": [],
                    "areas_for_growth": ["Needs to provide a response to be evaluated."]
                }
            
            # Create a comprehensive evaluation prompt
            eval_prompt = f"""
            You are evaluating a candidate's response to a behavioral question for a {level}-level position.
            
            Behavioral Question: {question_text}
            
            Question Context: {context}
            
            Evaluation Points:
            {', '.join([f"- {point}" for point in evaluation_points])}
            
            Passion Indicators to Look For:
            {', '.join([f"- {ind}" for ind in passion_indicators])}
            
            Cultural Fit Markers:
            {', '.join([f"- {marker}" for marker in cultural_fit_markers])}
            
            Candidate's Response:
            {candidate_answer}
            
            IMPORTANT: You must respond with ONLY a JSON object containing the evaluation. Format your response as valid JSON like this:
            {{
                "score": int,  // A value from 0 to {max_score}
                "communication": float,  // A value from 0.0 to 1.0
                "experience_relevance": float,  // A value from 0.0 to 1.0
                "problem_solving": float,  // A value from 0.0 to 1.0
                "leadership": float,  // A value from 0.0 to 1.0
                "passion_indicators": ["Indicator 1", "Indicator 2"],
                "feedback": "Your detailed feedback here",
                "strengths": ["Strength 1", "Strength 2"],
                "areas_for_growth": ["Area 1", "Area 2"]
            }}
            
            Do not include any explanations before or after the JSON. Only return the JSON object.
            """
            
            # Send to the LLM for evaluation
            logger.debug(f"Sending behavioral reasoning prompt for evaluation:\n{eval_prompt}")
            llm_response = await self.llm.ainvoke(eval_prompt)
            raw_content = llm_response.content
            
            # Extract and parse JSON
            parsed_json = self._extract_json(raw_content)
            
            if parsed_json:
                 logger.info(f"Successfully parsed behavioral evaluation for question ID {question_data.get('id')}")
                 
                 # Normalize the score to 0-100 scale if needed
                 if "score" in parsed_json and parsed_json["score"] < 100:
                     # If the score is less than 100, assume it's on the max_score scale
                     if parsed_json["score"] > max_score:
                         # Cap at max_score if needed
                         parsed_json["score"] = max_score
                     
                     # Convert to 0-100 scale
                     parsed_json["score"] = int((parsed_json["score"] / max_score) * 100)
                 
                 return parsed_json
            else:
                 logger.error(f"Could not parse JSON from behavioral evaluation. Raw content was:\n{raw_content}")
                 
                 # Try to create a more basic evaluation based on the response
                 fallback_response = self._create_fallback_behavioral_evaluation(candidate_answer, max_score)
                 logger.info(f"Created fallback evaluation for question ID {question_data.get('id')}")
                 return fallback_response
            
        except Exception as e:
            logger.error(f"Error in behavioral evaluation: {str(e)}", exc_info=True)
            return {
                "score": 0,
                "communication": 0.0,
                "experience_relevance": 0.0,
                "problem_solving": 0.0,
                "leadership": 0.0,
                "passion_indicators": [],
                "feedback": f"Error evaluating answer: {str(e)}",
                "strengths": [],
                "areas_for_growth": []
            }
    
    def _create_fallback_behavioral_evaluation(self, candidate_answer: str, max_score: int) -> Dict[str, Any]:
        """Create a fallback evaluation when JSON parsing fails"""
        if not candidate_answer or candidate_answer.strip() == "":
            # Empty response
            return {
                "score": 0,
                "communication": 0.0,
                "experience_relevance": 0.0,
                "problem_solving": 0.0,
                "leadership": 0.0,
                "passion_indicators": [],
                "feedback": "No response provided.",
                "strengths": [],
                "areas_for_growth": ["Needs to provide a response to be evaluated."]
            }
        
        # Very basic analysis - at least they answered something
        answer_length = len(candidate_answer.split())
        
        if answer_length < 20:
            # Very short answer
            score = max(10, int(max_score * 0.2))
            return {
                "score": score,
                "communication": 0.2,
                "experience_relevance": 0.1,
                "problem_solving": 0.1,
                "leadership": 0.1,
                "passion_indicators": [],
                "feedback": "Response is too brief to properly evaluate.",
                "strengths": ["Provided an answer"],
                "areas_for_growth": ["Provide more detailed responses", "Include specific examples"]
            }
        else:
            # Longer answer but we couldn't parse it - give them some benefit of the doubt
            score = max(40, int(max_score * 0.4))
            return {
                "score": score,
                "communication": 0.5,
                "experience_relevance": 0.4,
                "problem_solving": 0.4,
                "leadership": 0.3,
                "passion_indicators": ["Detailed response"],
                "feedback": "Response shows effort, but could not be fully evaluated.",
                "strengths": ["Provided a detailed answer"],
                "areas_for_growth": ["Structure responses clearly", "Focus on relevant experiences"]
            }

    async def evaluate_assessment(
        self,
        assessment: Assessment,
        candidate_answers: Dict[str, str]
    ) -> AssessmentResult:
        """Evaluate complete assessment and generate final result with safer key access."""
        logger.info(f"Starting full assessment evaluation for Assessment ID: {assessment.id}, Candidate: {assessment.candidate_name}")
        
        question_scores = {}
        feedback = {}
        technical_ratings = []
        passion_indicators_found = [] # Renamed for clarity
        
        all_questions = (
            [(q, "coding") for q in assessment.coding_questions] +
            [(q, "system_design") for q in assessment.system_design_questions] +
            [(q, "behavioral") for q in assessment.behavioral_questions]
        )

        for question, q_type in all_questions:
            if question.id in candidate_answers:
                logger.info(f"Evaluating answer for Question ID: {question.id} (Type: {q_type})")
                # Convert Pydantic model to dict safely for evaluation
                # Using model_dump() is preferred over __dict__ for Pydantic v2+
                question_dict = question.model_dump() if hasattr(question, 'model_dump') else question.__dict__
                
                result = await self.evaluate_answer(
                    q_type,
                    question_dict,
                    candidate_answers[question.id],
                    assessment.experience_level
                )
                
                # Use .get() for safer access to potentially missing keys
                score = result.get("score", 0) # Default to 0 if score key is missing
                feedback_text = result.get("feedback", "N/A") # Default feedback
                
                question_scores[question.id] = score 
                feedback[question.id] = feedback_text
                logger.info(f"Question ID: {question.id} evaluated. Score: {score}")

                # Collect ratings based on type, using .get()
                if q_type == "coding":
                    technical_ratings.append(result.get("technical_accuracy", 0.0))
                elif q_type == "system_design":
                    technical_ratings.append(result.get("architecture_quality", 0.0))
                    technical_ratings.append(result.get("scalability_consideration", 0.0))
                elif q_type == "behavioral":
                    # Assuming passion_indicators is a list of strings
                    indicators = result.get("passion_indicators", []) 
                    if isinstance(indicators, list):
                         passion_indicators_found.extend(indicators)
                    else:
                        logger.warning(f"Expected 'passion_indicators' to be a list for QID {question.id}, but got {type(indicators)}")
                        
            else:
                 logger.warning(f"No answer found for Question ID: {question.id}. Skipping evaluation.")
                 question_scores[question.id] = 0 # Assign 0 score if no answer
                 feedback[question.id] = "No answer provided."


        # Calculate final scores
        total_score = 0
        num_scored_questions = len([s for s in question_scores.values() if s is not None]) # Count only evaluated questions
        if num_scored_questions > 0:
            total_score = sum(question_scores.values()) / num_scored_questions
            logger.info(f"Calculated total score: {total_score:.2f} based on {num_scored_questions} answers.")
        else:
             logger.warning("No questions were scored.")
        
        avg_technical = 0
        if technical_ratings:
            avg_technical = sum(technical_ratings) / len(technical_ratings)
            logger.info(f"Calculated average technical rating: {avg_technical:.2f}")
            
        # Simple passion rating based on count of indicators found across all behavioral q's
        # Adjust this logic if a more nuanced approach is needed
        passion_rating = min(len(passion_indicators_found) / 5.0, 1.0) # Normalize based on an arbitrary max (e.g., 5 indicators)
        logger.info(f"Found {len(passion_indicators_found)} passion indicators. Calculated passion rating: {passion_rating:.2f}")
            
        # Determine pass/fail based on config
        passing_score_config = ASSESSMENT_CONFIG.get(assessment.experience_level, {})
        default_passing_percentage = ASSESSMENT_CONFIG.get("passing_score_percentage", 70) # Default if level or global default missing
        passing_percentage = passing_score_config.get("passing_score_percentage", default_passing_percentage)
        
        passed = total_score >= passing_percentage
        logger.info(f"Passing score percentage: {passing_percentage}. Candidate passed: {passed}")

        return AssessmentResult(
            assessment_id=assessment.id,
            candidate_name=assessment.candidate_name,
            score=int(round(total_score)),  # Convert to int after rounding
            passed=passed,
            question_scores=question_scores,
            feedback=feedback,
            technical_rating=round(avg_technical, 2),
            passion_rating=round(passion_rating, 2) # Use calculated passion rating
        )

    def generate_summary_report(self, result: AssessmentResult) -> str:
        """Generate a comprehensive human-readable summary report"""
        
        # Get current datetime for report generation timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Collect feedback points and organize by question type
        coding_strengths = []
        coding_improvements = []
        design_strengths = []
        design_improvements = []
        behavioral_strengths = []
        behavioral_improvements = []
        
        coding_scores = []
        design_scores = []
        behavioral_scores = []
        
        # Categorize questions by their IDs
        for qid, score in result.question_scores.items():
            if qid.startswith("code_"):
                coding_scores.append(score)
                if score >= 80:
                    coding_strengths.append(f"Strong performance in {qid}")
                elif score <= 60:
                    coding_improvements.append(f"Needs improvement in {qid}")
            elif qid.startswith("design_"):
                design_scores.append(score)
                if score >= 80:
                    design_strengths.append(f"Strong performance in {qid}")
                elif score <= 60:
                    design_improvements.append(f"Needs improvement in {qid}")
            elif qid.startswith("behavior_"):
                behavioral_scores.append(score)
                if score >= 80:
                    behavioral_strengths.append(f"Strong performance in {qid}")
                elif score <= 60:
                    behavioral_improvements.append(f"Needs improvement in {qid}")
        
        # Calculate average scores by category
        avg_coding_score = sum(coding_scores) / len(coding_scores) if coding_scores else 0
        avg_design_score = sum(design_scores) / len(design_scores) if design_scores else 0
        avg_behavioral_score = sum(behavioral_scores) / len(behavioral_scores) if behavioral_scores else 0
        
        # Add ratings-based feedback
        if result.technical_rating >= 0.8:
            coding_strengths.append("Strong technical capabilities demonstrated")
            design_strengths.append("Well-designed system architecture solutions")
        elif result.technical_rating <= 0.5:
            coding_improvements.append("Technical skills need significant improvement")
            design_improvements.append("System architecture understanding needs development")
            
        if result.passion_rating >= 0.8:
            behavioral_strengths.append("Shows strong enthusiasm and genuine interest in the role")
            behavioral_strengths.append("Demonstrates excellent cultural fit indicators")
        elif result.passion_rating <= 0.5:
            behavioral_improvements.append("Could demonstrate more passion for the role")
            behavioral_improvements.append("Consider highlighting motivations and interest in future interviews")
        
        # Format detailed feedback by category
        coding_feedback = []
        design_feedback = []
        behavioral_feedback = []
        
        for qid, score in result.question_scores.items():
            feedback = result.feedback.get(qid, "No feedback provided.")
            
            # Format based on question type
            if qid.startswith("code_"):
                coding_feedback.append(f"\nQuestion ID: {qid}")
                coding_feedback.append(f"Score: {score}/100")
                coding_feedback.append(f"Feedback: {feedback}")
            elif qid.startswith("design_"):
                design_feedback.append(f"\nQuestion ID: {qid}")
                design_feedback.append(f"Score: {score}/100")
                design_feedback.append(f"Feedback: {feedback}")
            elif qid.startswith("behavior_"):
                behavioral_feedback.append(f"\nQuestion ID: {qid}")
                behavioral_feedback.append(f"Score: {score}/100")
                behavioral_feedback.append(f"Feedback: {feedback}")

        # Format strengths and improvements by category
        coding_strength_items = [f"- {s}" for s in coding_strengths] if coding_strengths else ["- None identified"]
        coding_improvement_items = [f"- {i}" for i in coding_improvements] if coding_improvements else ["- None identified"]
        
        design_strength_items = [f"- {s}" for s in design_strengths] if design_strengths else ["- None identified"]
        design_improvement_items = [f"- {i}" for i in design_improvements] if design_improvements else ["- None identified"]
        
        behavioral_strength_items = [f"- {s}" for s in behavioral_strengths] if behavioral_strengths else ["- None identified"]
        behavioral_improvement_items = [f"- {i}" for i in behavioral_improvements] if behavioral_improvements else ["- None identified"]
        
        # Performance analytics
        skill_areas = [
            ("Coding", avg_coding_score),
            ("System Design", avg_design_score),
            ("Behavioral", avg_behavioral_score)
        ]
        
        # Identify strongest and weakest areas
        skill_areas.sort(key=lambda x: x[1], reverse=True)
        strongest_area = skill_areas[0][0] if skill_areas[0][1] > 0 else "None"
        weakest_area = skill_areas[-1][0] if skill_areas[-1][1] > 0 else "None"
        
        # Recommendations based on scores and analytics
        recommendations = [
            f"- {'Proceed with next interview stage' if result.passed else 'Consider additional preparation before proceeding'}",
            f"- Focus on strengthening skills in {weakest_area.lower()} questions",
            f"- {'Continue to leverage strong performance in ' + strongest_area.lower() + ' questions' if skill_areas[0][1] >= 70 else 'Work on improving all areas with focused study'}",
            f"- {'Focus on practical implementation' if result.technical_rating < 0.7 else 'Continue building on strong technical foundation'}",
            f"- {'Show more enthusiasm in responses' if result.passion_rating < 0.7 else 'Maintain strong engagement level'}"
        ]
        
        # Combine all sections for the report
        report_sections = [
            f"Assessment Summary for {result.candidate_name}",
            "=" * (20 + len(result.candidate_name)),
            f"Generated on: {timestamp}",
            f"Assessment ID: {result.assessment_id}",
            "",
            "OVERALL RESULTS",
            "=" * 14,
            f"Total Score: {result.score}/100",
            f"Status: {'PASSED ✓' if result.passed else 'FAILED ✗'}",
            f"Technical Rating: {result.technical_rating:.2f}/1.0",
            f"Passion Rating: {result.passion_rating:.2f}/1.0",
            "",
            "PERFORMANCE BY CATEGORY",
            "=" * 23,
            f"Coding Questions:     {avg_coding_score:.1f}/100",
            f"System Design:        {avg_design_score:.1f}/100",
            f"Behavioral Questions: {avg_behavioral_score:.1f}/100",
            "",
            f"Strongest Area: {strongest_area}",
            f"Needs Improvement: {weakest_area}" if skill_areas[-1][1] < 70 else "No significant weak areas identified",
            "",
            "DETAILED FEEDBACK BY CATEGORY",
            "=" * 29,
        ]
        
        # Add Coding section if we have any coding questions
        if coding_feedback:
            report_sections.extend([
                "",
                "CODING QUESTIONS",
                "-" * 15,
                "Average Score: " + f"{avg_coding_score:.1f}/100"
            ])
            report_sections.extend(coding_feedback)
            report_sections.extend([
                "",
                "Coding Strengths:"
            ])
            report_sections.extend(coding_strength_items)
            report_sections.extend([
                "",
                "Coding Areas for Improvement:"
            ])
            report_sections.extend(coding_improvement_items)
        
        # Add System Design section if we have any design questions
        if design_feedback:
            report_sections.extend([
                "",
                "SYSTEM DESIGN QUESTIONS",
                "-" * 22,
                "Average Score: " + f"{avg_design_score:.1f}/100"
            ])
            report_sections.extend(design_feedback)
            report_sections.extend([
                "",
                "System Design Strengths:"
            ])
            report_sections.extend(design_strength_items)
            report_sections.extend([
                "",
                "System Design Areas for Improvement:"
            ])
            report_sections.extend(design_improvement_items)
        
        # Add Behavioral section if we have any behavioral questions
        if behavioral_feedback:
            report_sections.extend([
                "",
                "BEHAVIORAL QUESTIONS",
                "-" * 20,
                "Average Score: " + f"{avg_behavioral_score:.1f}/100"
            ])
            report_sections.extend(behavioral_feedback)
            report_sections.extend([
                "",
                "Behavioral Strengths:"
            ])
            report_sections.extend(behavioral_strength_items)
            report_sections.extend([
                "",
                "Behavioral Areas for Improvement:"
            ])
            report_sections.extend(behavioral_improvement_items)
        
        # Add summary and recommendations section
        report_sections.extend([
            "",
            "SUMMARY & RECOMMENDATIONS",
            "=" * 25,
            "Key Strengths:",
            "- " + (strongest_area if skill_areas[0][1] >= 70 else "No outstanding strengths identified"),
            f"- {'Technical knowledge is solid' if result.technical_rating >= 0.7 else 'Basic technical understanding demonstrated'}",
            f"- {'Shows genuine passion for the role' if result.passion_rating >= 0.7 else 'Professional attitude demonstrated'}",
            "",
            "Areas for Improvement:",
            "- " + (weakest_area if skill_areas[-1][1] < 70 else "No critical weaknesses identified"),
            f"- {'Technical skills could be stronger' if result.technical_rating < 0.7 else 'Continue technical development'}",
            f"- {'Could show more enthusiasm' if result.passion_rating < 0.7 else 'Maintain positive attitude'}",
            "",
            "Recommendations:",
        ])
        report_sections.extend(recommendations)
        
        # Add footer
        report_sections.extend([
            "",
            "=" * 50,
            "This report was automatically generated based on the assessment responses.",
            "Results should be considered alongside other evaluation methods.",
            "Assessment conducted via AI-powered Online Assessment Module",
            "=" * 50,
        ])
        
        return "\n".join(report_sections)