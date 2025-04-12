# agents/question_generator.py

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
import json
import uuid
from models.data_models import (
    CodingQuestion,
    SystemDesignQuestion,
    BehavioralQuestion,
    Assessment
)
from config import NON_REASONING_MODEL, API_CONFIG, ASSESSMENT_CONFIG, QUESTION_WEIGHTS

# Configure logger
logger = logging.getLogger(__name__)

class QuestionGenerator:
    """
    Generates assessment questions based on candidate profile and job requirements.
    Uses a simplified, reliable approach to generate well-formed questions.
    """
    
    def __init__(self, api_key: str):
        """Initialize with API key"""
        self.llm = ChatOpenAI(
            model=NON_REASONING_MODEL,
            temperature=0.1,  # Lower temperature for more consistent output
            openai_api_key=api_key,
            openai_api_base=API_CONFIG["non_reasoning"]["base_url"]
        )
        
    async def generate_assessment(
        self,
        candidate_name: str,
        job_title: str,
        skills: List[str],
        experience: List[Dict[str, Any]],
        level: str,
        job_requirements: Dict[str, Any],
        candidate_profile: Dict[str, Any]
    ) -> Assessment:
        """
        Generate a complete assessment for a candidate
        """
        logger.info(f"Generating assessment for {candidate_name}, level: {level}")
        
        # Validate and normalize level
        if not level or level not in ["junior", "mid", "senior"]:
            logger.warning(f"Invalid level '{level}', using 'mid' as default")
            level = "mid"
            
        # Get question counts based on level
        config = ASSESSMENT_CONFIG.get(level, ASSESSMENT_CONFIG["mid"])
        
        # Create tasks for concurrent question generation
        coding_tasks = []
        for i in range(config["coding_questions"]):
            coding_tasks.append(self._create_coding_question(skills, level))
        
        design_tasks = []
        for i in range(config["system_design_questions"]):
            design_tasks.append(self._create_system_design_question(level))
        
        behavioral_tasks = []
        for i in range(config["behavioral_questions"]):
            behavioral_tasks.append(self._create_behavioral_question(level))
        
        # Run all question generation tasks concurrently
        try:
            # Execute tasks in batches to avoid rate limiting
            coding_questions = []
            design_questions = []
            behavioral_questions = []
            
            # Generate coding questions (in batches of 2)
            for i in range(0, len(coding_tasks), 2):
                batch = coding_tasks[i:i+2]
                results = await asyncio.gather(*batch, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error generating coding question: {str(result)}")
                        coding_questions.append(self._fallback_coding_question(level))
                    else:
                        coding_questions.append(result)
            
            # Generate system design questions (in batches of 2)
            for i in range(0, len(design_tasks), 2):
                batch = design_tasks[i:i+2]
                results = await asyncio.gather(*batch, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error generating system design question: {str(result)}")
                        design_questions.append(self._fallback_system_design_question(level))
                    else:
                        design_questions.append(result)
            
            # Generate behavioral questions (in batches of 2)
            for i in range(0, len(behavioral_tasks), 2):
                batch = behavioral_tasks[i:i+2]
                results = await asyncio.gather(*batch, return_exceptions=True)
                for result in results:
                    if isinstance(result, Exception):
                        logger.error(f"Error generating behavioral question: {str(result)}")
                        behavioral_questions.append(self._fallback_behavioral_question(level))
                    else:
                        behavioral_questions.append(result)
                
        except Exception as e:
            logger.error(f"Error in concurrent question generation: {str(e)}")
            # Provide fallback questions if the concurrent approach fails
            coding_questions = [self._fallback_coding_question(level) for _ in range(config["coding_questions"])]
            design_questions = [self._fallback_system_design_question(level) for _ in range(config["system_design_questions"])]
            behavioral_questions = [self._fallback_behavioral_question(level) for _ in range(config["behavioral_questions"])]
        
        # Calculate scores
        total_score = sum([q.score for q in coding_questions + design_questions + behavioral_questions])
        passing_threshold = ASSESSMENT_CONFIG.get("passing_score_percentage", 70)
        passing_score = int(total_score * (passing_threshold / 100))
        
        # Create assessment object
        assessment = Assessment(
            candidate_name=candidate_name or "Candidate",
            job_title=job_title or "Software Engineer",
            experience_level=level,
            coding_questions=coding_questions,
            system_design_questions=design_questions,
            behavioral_questions=behavioral_questions,
            total_score=total_score,
            passing_score=passing_score
        )
        
        return assessment
    
    async def _create_coding_question(self, skills: List[str], level: str) -> CodingQuestion:
        """Create a coding question for the specified skill level"""
        skill_list = ", ".join(skills[:3]) if skills else "Programming"
        
        # Create a list of varied question topics to ensure diversity
        coding_topics = [
            "algorithms and data structures",
            "object-oriented programming concepts",
            "API design principles",
            "concurrency and multithreading",
            "database query optimization",
            "memory management",
            "error handling best practices",
            "design patterns",
            "functional programming concepts",
            "testing and debugging techniques"
        ]
        
        # Select a random topic based on the question index (using a UUID for randomness)
        random_seed = int(uuid.uuid4().hex[:8], 16) % len(coding_topics)
        selected_topic = coding_topics[random_seed]
        
        template = """
        Create a technical multiple-choice coding question for a {level} level software engineer with skills in {skills}.
        
        The question should focus on the topic of {topic}.
        
        Make the question specific, interesting, and challenging for the candidate.
        
        Each option should be a code snippet, algorithm approach, or technical concept.
        
        Your response should include the following:
        - A clear question text
        - Four distinct answer options labeled as 'Option A', 'Option B', 'Option C', and 'Option D'
        - The index of the correct answer (0, 1, 2, or 3)
        - A brief explanation of the correct answer
        - Difficulty level (easy, medium, or hard)
        - Skills being tested
        - What this question indicates about the candidate's abilities
        
        Example format:
        text: What is the time complexity of quicksort in the worst case?
        options: 
        - Option A: O(n)
        - Option B: O(n log n)
        - Option C: O(n^2)
        - Option D: O(2^n)
        correct_option: 2
        explanation: Quicksort has O(n^2) worst-case complexity when the pivot selection is poor
        difficulty: medium
        skills_tested: Algorithms, Time Complexity
        performance_indicators: Algorithm Analysis, Computer Science Fundamentals
        """
        
        question_json = await self._generate_structured_response(
            template, 
            {"level": level, "skills": skill_list, "topic": selected_topic},
            temperature=0.7  # Higher temperature for more variety
        )
        
        # Ensure options are properly formatted
        default_options = [
            "Option A: return array.sort()",
            "Option B: use quicksort algorithm", 
            "Option C: implement merge sort", 
            "Option D: use binary search tree"
        ]
        
        options = question_json.get("options", default_options)
        
        # If options are empty strings or not properly formatted, use defaults
        if not options or len(options) < 4 or any(not isinstance(opt, str) or not opt.strip() for opt in options):
            logger.warning("Received invalid options for coding question, using defaults")
            options = default_options
        
        # Ensure each option has the proper prefix
        for i in range(len(options)):
            if i < len(options) and not options[i].startswith(f"Option {chr(65+i)}:"):
                options[i] = f"Option {chr(65+i)}: {options[i]}"
        
        # Pad the options to ensure we have at least 4
        while len(options) < 4:
            options.append(f"Option {chr(65+len(options))}: Additional coding approach")
        
        # Ensure correct_option is valid
        correct_option = question_json.get("correct_option", 0)
        if not isinstance(correct_option, int) or correct_option < 0 or correct_option >= len(options):
            correct_option = 0
        
        # Default weight based on level
        weights = QUESTION_WEIGHTS["coding"][level]
        score = weights["min"]
        if "difficulty" in question_json:
            if question_json["difficulty"] == "hard":
                score = weights["max"]
            elif question_json["difficulty"] == "medium":
                score = (weights["min"] + weights["max"]) // 2
        
        # Create the question object with a unique ID
        return CodingQuestion(
            id=f"code_{uuid.uuid4().hex[:8]}",
            type="coding",
            text=question_json.get("text", f"Write a function related to {skill_list}"),
            options=options[:4],  # Ensure exactly 4 options
            correct_option=correct_option,
            explanation=question_json.get("explanation", "This tests programming fundamentals"),
            difficulty=question_json.get("difficulty", "medium"),
            score=score,
            skills_tested=question_json.get("skills_tested", skills[:2] if skills else ["Programming"]),
            performance_indicators=question_json.get("performance_indicators", ["Problem Solving", "Technical Knowledge"])
        )
    
    async def _create_system_design_question(self, level: str) -> SystemDesignQuestion:
        """Create a system design question based on experience level"""
        
        # Create a list of varied system design scenarios to ensure diversity
        design_scenarios = [
            "e-commerce platform",
            "social media application",
            "real-time chat system",
            "video streaming service",
            "ride-sharing application",
            "content delivery network",
            "distributed database",
            "AI recommendation engine",
            "mobile payment system",
            "IoT device management platform",
            "analytics dashboard",
            "file sharing service",
            "collaborative document editing",
            "online multiplayer game"
        ]
        
        # Select a random scenario based on the question index
        random_seed = int(uuid.uuid4().hex[:8], 16) % len(design_scenarios)
        selected_scenario = design_scenarios[random_seed]
        
        template = """
        Create a unique system design question for a {level} level software engineer.
        
        IMPORTANT: Focus on designing a {scenario} and make sure this question is specific and different from generic system design questions.
        
        The question should test architectural understanding and system design principles.
        
        Respond with ONLY the following fields:
        - text: The question text
        - scenario: Brief context for the design
        - requirements: Key requirements to consider (array)
        - expected_components: Components expected in the solution (array)
        - evaluation_criteria: How to evaluate the answer (array)
        - difficulty: easy, medium, or hard
        - architectural_focus: Architectural areas being tested (array)
        """
        
        question_json = await self._generate_structured_response(
            template, 
            {"level": level, "scenario": selected_scenario},
            temperature=0.7  # Higher temperature for more variety
        )
        
        # Default weight based on level
        weights = QUESTION_WEIGHTS["system_design"][level]
        score = weights["min"]
        if "difficulty" in question_json:
            if question_json["difficulty"] == "hard":
                score = weights["max"]
            elif question_json["difficulty"] == "medium":
                score = (weights["min"] + weights["max"]) // 2
        
        # Create the question object with a unique ID
        return SystemDesignQuestion(
            id=f"design_{uuid.uuid4().hex[:8]}",
            type="system_design",
            text=question_json.get("text", f"Design a {selected_scenario} for a {level}-level challenge"),
            scenario=question_json.get("scenario", f"Design a {selected_scenario} that handles high traffic"),
            requirements=question_json.get("requirements", ["Scalability", "Reliability"]),
            expected_components=question_json.get("expected_components", ["Load Balancer", "Database", "Cache"]),
            evaluation_criteria=question_json.get("evaluation_criteria", ["Architecture", "Scalability"]),
            difficulty=question_json.get("difficulty", "medium"),
            score=score,
            architectural_focus=question_json.get("architectural_focus", ["Scalability", "Performance"])
        )
    
    async def _create_behavioral_question(self, level: str) -> BehavioralQuestion:
        """Create a behavioral question appropriate for the experience level"""
        
        # Create a list of varied behavioral question themes to ensure diversity
        behavioral_themes = [
            "teamwork and collaboration",
            "leadership and initiative",
            "conflict resolution",
            "adaptability and learning",
            "communication skills",
            "problem-solving approach",
            "time management",
            "handling pressure and deadlines",
            "receiving and implementing feedback",
            "technical mentorship",
            "innovation and creativity",
            "ethical decision making",
            "project management"
        ]
        
        # Select a random theme based on the question index
        random_seed = int(uuid.uuid4().hex[:8], 16) % len(behavioral_themes)
        selected_theme = behavioral_themes[random_seed]
        
        template = """
        Create a unique behavioral interview question for a {level} level software engineer.
        
        IMPORTANT: Focus on the theme of {theme} and make sure this question is specific and different from standard behavioral questions.
        Avoid generic questions like "Tell me about a time you worked on a team."
        
        The question should assess soft skills, teamwork, and problem-solving approach.
        
        Respond with ONLY the following fields:
        - text: The question text
        - context: Brief context for the question
        - evaluation_points: What to look for in the answer (array)
        - passion_indicators: Indicators of passion (array)
        - cultural_fit_markers: Indicators of cultural fit (array)
        - difficulty: easy, medium, or hard
        """
        
        question_json = await self._generate_structured_response(
            template, 
            {"level": level, "theme": selected_theme},
            temperature=0.7  # Higher temperature for more variety
        )
        
        # Default weight based on level
        weights = QUESTION_WEIGHTS["behavioral"][level]
        score = weights["min"]
        if "difficulty" in question_json:
            if question_json["difficulty"] == "hard":
                score = weights["max"]
            elif question_json["difficulty"] == "medium":
                score = (weights["min"] + weights["max"]) // 2
        
        # Create the question object with a unique ID
        return BehavioralQuestion(
            id=f"behavior_{uuid.uuid4().hex[:8]}",
            type="behavioral",
            text=question_json.get("text", f"Describe an experience related to {selected_theme}"),
            context=question_json.get("context", f"Assessing {selected_theme}"),
            evaluation_points=question_json.get("evaluation_points", ["Problem Analysis", "Solution Approach"]),
            passion_indicators=question_json.get("passion_indicators", ["Enthusiasm", "Initiative"]),
            cultural_fit_markers=question_json.get("cultural_fit_markers", ["Teamwork", "Communication"]),
            difficulty=question_json.get("difficulty", "medium"),
            score=score
        )
    
    async def _generate_structured_response(self, template: str, params: Dict[str, Any], temperature: float = 0.1) -> Dict[str, Any]:
        """Helper method to generate structured responses from the LLM"""
        prompt = PromptTemplate.from_template(template)
        formatted_prompt = prompt.format(**params)
        
        try:
            # Create a temporary LLM with the specified temperature for this call
            temp_llm = ChatOpenAI(
                model=NON_REASONING_MODEL,
                temperature=temperature,  # Use the provided temperature
                openai_api_key=self.llm.openai_api_key,
                openai_api_base=API_CONFIG["non_reasoning"]["base_url"]
            )
            
            response = await temp_llm.ainvoke(formatted_prompt)
            content = response.content.strip()
            
            # Initialize result dictionary
            result = {}
            
            # Try to parse as JSON first
            try:
                if content.startswith("{") and content.endswith("}"):
                    return json.loads(content)
            except:
                logger.debug("Content not valid JSON, attempting other parsing methods")
            
            # Parse YAML-like format (most common response format)
            try:
                lines = content.split('\n')
                current_key = None
                current_list = None
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        continue
                        
                    # Check if this is a key-value pair (text: value)
                    if ":" in line and not line.startswith("-"):
                        parts = line.split(":", 1)
                        key = parts[0].strip().lower().replace(" ", "_")
                        value = parts[1].strip() if len(parts) > 1 else ""
                        
                        # Start a new key
                        result[key] = value
                        current_key = key
                        
                        # If the value is empty, this might be the start of a list
                        if not value:
                            current_list = []
                            result[current_key] = current_list
                        else:
                            current_list = None
                    
                    # Check if this is a list item (- item)
                    elif line.startswith("-") and current_key:
                        item = line[1:].strip()
                        if current_list is not None:
                            current_list.append(item)
                        elif isinstance(result.get(current_key), list):
                            result[current_key].append(item)
                        else:
                            current_list = [item]
                            result[current_key] = current_list
            
                # Fix specific fields
                # Convert options to the right format if they're in a list
                if "options" in result and isinstance(result["options"], list):
                    for i, option in enumerate(result["options"]):
                        if not option.startswith(f"Option {chr(65+i)}:"):
                            result["options"][i] = f"Option {chr(65+i)}: {option}"
                
                # Convert correct_option to int
                if "correct_option" in result:
                    try:
                        result["correct_option"] = int(result["correct_option"])
                    except:
                        result["correct_option"] = 0
                
                # Handle skills_tested and performance_indicators
                for list_field in ["skills_tested", "performance_indicators"]:
                    if list_field in result and isinstance(result[list_field], str):
                        # Split comma-separated values
                        result[list_field] = [item.strip() for item in result[list_field].split(",")]
                
                logger.debug(f"Successfully parsed YAML-like content into {len(result)} fields")
                return result
                
            except Exception as yaml_error:
                logger.warning(f"Error parsing YAML-like content: {str(yaml_error)}")
            
            # Fallback to extracting key/value pairs from the text
            try:
                # Simple key-value extraction as last resort
                result = {}
                lines = content.strip().split('\n')
                
                for line in lines:
                    line = line.strip()
                    if ':' in line and not line.startswith('-'):
                        key, value = line.split(':', 1)
                        key = key.strip().lower().replace(' ', '_')
                        value = value.strip().strip('"\'')
                        if value:
                            result[key] = value
            except:
                logger.warning("Failed to extract key-value pairs from content")
                
            # For coding questions, ensure options are present with context-aware defaults
            if "options" not in result or not result["options"]:
                topic = params.get("topic", "algorithms")
                level = params.get("level", "mid")
                result["options"] = self._get_topic_specific_options(topic, level)
            
            # Ensure required fields
            if "text" not in result:
                topic = params.get("topic", "algorithms")
                result["text"] = f"What is the best approach for implementing {topic}?"
                
            if "correct_option" not in result:
                result["correct_option"] = 0
                
            return result
            
        except Exception as e:
            logger.error(f"Error generating structured response: {str(e)}")
            # Always provide fallback options for coding questions that are specific to the topic
            topic = params.get("topic", "algorithms")
            level = params.get("level", "mid")
            return {
                "options": self._get_topic_specific_options(topic, level),
                "correct_option": 0,
                "text": f"What is the best approach for implementing {topic}?",
                "explanation": f"This tests understanding of {topic} principles."
            }
            
    def _get_topic_specific_options(self, topic: str, level: str) -> List[str]:
        """Generate context-aware options based on the question topic"""
        
        # Define option templates for different topics
        topic_options = {
            "algorithms and data structures": [
                "Option A: Use a hash table for O(1) lookup time",
                "Option B: Implement a binary search for O(log n) time complexity",
                "Option C: Use a linked list to maintain insertion order",
                "Option D: Apply dynamic programming to solve the subproblems"
            ],
            "object-oriented programming": [
                "Option A: Create a class hierarchy with inheritance",
                "Option B: Use composition instead of inheritance",
                "Option C: Implement an interface to define the contract",
                "Option D: Apply the singleton pattern to ensure a single instance"
            ],
            "concurrency": [
                "Option A: Use a mutex to protect the shared resource",
                "Option B: Implement a thread pool to manage worker threads",
                "Option C: Use atomic operations to prevent race conditions",
                "Option D: Apply the actor model for message passing between threads"
            ],
            "memory management": [
                "Option A: Use reference counting for automatic cleanup",
                "Option B: Implement a garbage collector to reclaim memory",
                "Option C: Use smart pointers to manage object lifetimes",
                "Option D: Apply manual memory management with explicit allocation/deallocation"
            ],
            "design patterns": [
                "Option A: Apply the Factory pattern to create objects",
                "Option B: Use the Observer pattern for event handling",
                "Option C: Implement the Strategy pattern to select algorithms at runtime",
                "Option D: Use the Decorator pattern to extend functionality"
            ],
            "testing": [
                "Option A: Write unit tests for individual functions",
                "Option B: Implement integration tests for component interactions",
                "Option C: Use mock objects to simulate dependencies",
                "Option D: Apply test-driven development (TDD) principles"
            ]
        }
        
        # Find the closest matching topic
        best_match = "algorithms and data structures"  # Default
        for key in topic_options.keys():
            if key in topic.lower():
                best_match = key
                break
                
        # Return the options for the best matching topic
        return topic_options.get(best_match, [
            "Option A: Implement an efficient algorithm",
            "Option B: Use appropriate data structures",
            "Option C: Apply best practices for readability",
            "Option D: Optimize for performance and maintainability"
        ])
    
    def _fallback_coding_question(self, level: str) -> CodingQuestion:
        """Create a fallback coding question if generation fails"""
        weights = QUESTION_WEIGHTS["coding"][level]
        return CodingQuestion(
            id=f"code_{uuid.uuid4().hex[:8]}",
            type="coding",
            text="What is the time complexity of binary search?",
            options=[
                "Option A: O(1)",
                "Option B: O(log n)",
                "Option C: O(n)",
                "Option D: O(n log n)"
            ],
            correct_option=1,
            explanation="Binary search divides the search space in half with each comparison",
            difficulty="medium",
            score=weights["min"],
            skills_tested=["Algorithms", "Time Complexity"],
            performance_indicators=["Algorithm Knowledge", "Computational Thinking"]
        )
    
    def _fallback_system_design_question(self, level: str) -> SystemDesignQuestion:
        """Create a fallback system design question if generation fails"""
        weights = QUESTION_WEIGHTS["system_design"][level]
        return SystemDesignQuestion(
            id=f"design_{uuid.uuid4().hex[:8]}",
            type="system_design",
            text="Design a scalable web service that can handle millions of requests per day",
            scenario="You need to design a service that processes user requests and stores data reliably",
            requirements=["High Availability", "Scalability", "Data Consistency"],
            expected_components=["Load Balancer", "Application Servers", "Database", "Caching Layer"],
            evaluation_criteria=["Architecture Quality", "Scalability Approach", "Data Management"],
            difficulty="medium",
            score=weights["min"],
            architectural_focus=["Scalability", "Reliability", "Performance"]
        )
    
    def _fallback_behavioral_question(self, level: str) -> BehavioralQuestion:
        """Create a fallback behavioral question if generation fails"""
        weights = QUESTION_WEIGHTS["behavioral"][level]
        return BehavioralQuestion(
            id=f"behavior_{uuid.uuid4().hex[:8]}",
            type="behavioral",
            text="Describe a challenging technical problem you've solved and how you approached it",
            context="Assessing problem-solving methodology and technical depth",
            evaluation_points=["Problem Analysis", "Solution Approach", "Results Achieved"],
            passion_indicators=["Technical Enthusiasm", "Persistence", "Learning Motivation"],
            cultural_fit_markers=["Teamwork", "Communication", "Initiative"],
            difficulty="medium",
            score=weights["min"]
        )