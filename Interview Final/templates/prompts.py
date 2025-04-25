from langchain_core.prompts import PromptTemplate

# --- Parser Agent Prompts ---
PARSE_INPUT_PROMPT = PromptTemplate(
    input_variables=["content"],
    template="""
    You are a specialized parser that extracts structured information from text containing job descriptions, resumes, and assessment results.
    Analyze the following raw text content:

    {content}
    
    Extract and structure the information into these sections based on the ParsedInput Pydantic model:
    1. `job_description` (JobDescription model): Extract title, requirements, qualifications, etc.
    2. `resume_data` (ResumeData model): Extract personal info, education, experience, skills, projects, etc.
    3. `oa_results` (OAResult model): Extract the overall assessment results.
        - Extract `total_score` (integer) and `status` (string).
        - Look for a section detailing 'Performance by Category'. Parse the key-value pairs (e.g., 'Category Name: Score/Rating') into a JSON object for the `performance_by_category` field.
        - Look for a section detailing 'Detailed Feedback'. Parse the key-value pairs or bullet points into a JSON object for the `detailed_feedback` field.
        - Use 0.0 for `technical_rating` and `passion_rating` if not explicitly found.
        - If 'Performance by Category' or 'Detailed Feedback' sections are missing or empty, use an empty JSON object {{}} for the corresponding field.

    Return the entire extracted information as a single, clean JSON object matching the structure of the `ParsedInput` Pydantic model.
    Ensure all required fields from the models are present. Fill missing optional fields with appropriate defaults (e.g., empty lists [], empty strings "", empty objects {{}}, 0).
    Pay close attention to data types (string, integer, float, list, object/dictionary).
    """
)

# --- Interview Agent Prompts ---

TECHNICAL_QUESTION_PROMPT = PromptTemplate(
    input_variables=["job_description", "resume", "oa_results"],
    template="""
    Based on the following Job Description, Resume, and OA Results, generate exactly 5 technical interview questions suitable for assessing the candidate.

    JOB DESCRIPTION:
    {job_description}
    
    RESUME:
    {resume}
    
    OA RESULTS:
    {oa_results}
    
    Create questions that:
    1. Test core technical knowledge
    2. Relate to required skills/technologies
    3. Assess problem-solving ability
    4. Vary in difficulty
    5. Are relevant to the experience level
    
    Return exactly 5 questions in JSON format. Each JSON object MUST conform to the InterviewQuestion model structure, including ALL of the following fields:
    - "question": (string) The text of the question.
    - "category": (string) Set this to "technical".
    - "expected_answer": (string) A brief outline of the key points or concepts expected in a good answer.
    - "difficulty": (integer) An estimated difficulty level from 1 (easy) to 5 (hard).
    - "rationale": (string) A brief explanation of why this question is relevant or what it assesses.
    - "score": (integer) The point value for this question (e.g., 10 or 20).
    
    Example format for one question:
    {{
      "question": "Explain the difference between TCP and UDP.",
      "category": "technical",
      "expected_answer": "TCP: connection-oriented, reliable, ordered delivery. UDP: connectionless, unreliable, faster, suitable for streaming.",
      "difficulty": 2,
      "rationale": "Assesses fundamental networking knowledge.",
      "score": 10
    }}
    Ensure the entire output is a valid JSON list containing exactly 5 such objects.
    """
)

BEHAVIORAL_QUESTION_PROMPT = PromptTemplate(
    input_variables=["job_description", "resume", "oa_results"],
    template="""
    Based on the following Job Description, Resume, and OA Results, generate exactly 5 behavioral interview questions suitable for assessing the candidate's soft skills and cultural fit.

    JOB DESCRIPTION:
    {job_description}
    
    RESUME:
    {resume}
    
    OA RESULTS:
    {oa_results}
    
    Create questions that:
    1. Explore teamwork and collaboration
    2. Assess problem-solving approaches
    3. Evaluate communication skills
    4. Gauge adaptability and learning agility
    5. Align with company values (implicitly, based on typical corporate expectations)
    
    Return exactly 5 questions in JSON format. Each JSON object MUST conform to the InterviewQuestion model structure, including ALL of the following fields:
    - "question": (string) The text of the question.
    - "category": (string) Set this to "behavioral".
    - "expected_answer": (string) A brief description of the traits or skills the answer should demonstrate (e.g., "Demonstrates teamwork, conflict resolution").
    - "difficulty": (integer) An estimated difficulty level from 1 (easy) to 5 (hard) - typically 2-4 for behavioral.
    - "rationale": (string) A brief explanation of what competency this question targets (e.g., "Assesses collaboration skills").
    - "score": (integer) The point value for this question (e.g., 10 or 15).

    Example format for one question:
    {{
      "question": "Describe a time you disagreed with a team member. How did you handle it?",
      "category": "behavioral",
      "expected_answer": "Candidate should describe a specific situation, their approach (active listening, finding common ground), and a constructive outcome. Demonstrates conflict resolution and communication.",
      "difficulty": 3,
      "rationale": "Assesses conflict resolution and communication skills.",
      "score": 15
    }}
    Ensure the entire output is a valid JSON list containing exactly 5 such objects.
    """
)

SYSTEM_DESIGN_PROMPT = PromptTemplate(
    input_variables=["job_description", "resume", "oa_results", "level"],
    template="""
    Based on the following Job Description (especially experience level: {level}), Resume, and OA Results, generate exactly 5 system design interview questions.

    JOB DESCRIPTION:
    {job_description}
    
    RESUME:
    {resume}
    
    OA RESULTS:
    {oa_results}
    
    Create questions that:
    1. Assess architectural thinking
    2. Evaluate understanding of scalability and trade-offs
    3. Test knowledge of relevant technologies/patterns
    4. Require discussion of components and interactions
    5. Are appropriate for the candidate's experience level ({level})
    
    Return exactly 5 questions in JSON format. Each JSON object MUST conform to the InterviewQuestion model structure, including ALL of the following fields:
    - "question": (string) The system design problem statement (e.g., "Design a URL shortening service").
    - "category": (string) Set this to "system_design".
    - "expected_answer": (string) An outline of key areas to cover (e.g., "API design, data model, scaling strategy, load balancing, caching, trade-offs considered").
    - "difficulty": (integer) An estimated difficulty level from 1 (easy) to 5 (hard), appropriate for the {level} level.
    - "rationale": (string) A brief explanation of what aspects of design this question targets.
    - "score": (integer) The point value for this question (e.g., 20 or 30).

    Example format for one question:
    {{
      "question": "Design a real-time notification system.",
      "category": "system_design",
      "expected_answer": "Discuss requirements (types of notifications, delivery guarantees), components (message queue, pub/sub, WebSockets/SSE), scalability, reliability, data storage for user preferences.",
      "difficulty": 4,
      "rationale": "Assesses understanding of real-time architecture, messaging systems, and scalability.",
      "score": 25
    }}
    Ensure the entire output is a valid JSON list containing exactly 5 such objects.
    """
)

CODING_QUESTION_PROMPT = PromptTemplate(
    input_variables=["job_description", "resume", "oa_results", "level"],
    template="""
    Based on the following Job Description (especially experience level: {level}), Resume, and OA Results, generate exactly 5 coding interview questions (problem statements).

    JOB DESCRIPTION:
    {job_description}
    
    RESUME:
    {resume}
    
    OA RESULTS:
    {oa_results}
    
    Create questions that:
    1. Test problem-solving skills
    2. Cover relevant algorithms and data structures
    3. Include edge cases considerations implicitly
    4. Are solvable within a typical interview timeframe
    5. Are appropriate for the candidate's experience level ({level})
    
    Return exactly 5 questions in JSON format. Each JSON object MUST conform to the InterviewQuestion model structure, including ALL of the following fields:
    - "question": (string) The coding problem statement. **Use the key "question" for the problem statement, NOT "problem_statement".**
    - "category": (string) Set this to "coding".
    - "expected_answer": (string) A brief description of the optimal approach or algorithm (e.g., "Use a hash map for O(n) lookup", "Apply BFS traversal"). Include time/space complexity if appropriate.
    - "difficulty": (integer) An estimated difficulty level from 1 (easy) to 5 (hard), appropriate for the {level} level.
    - "rationale": (string) A brief explanation of what algorithm/data structure knowledge this question tests.
    - "score": (integer) The point value for this question (e.g., 15 or 25).

    Example format for one question:
    {{
      "question": "Given an array of integers nums and an integer target, return indices of the two numbers such that they add up to target.",
      "category": "coding",
      "expected_answer": "Use a hash map to store numbers seen and their indices. Iterate through the array, check if (target - current_num) exists in the map. O(n) time, O(n) space.",
      "difficulty": 2,
      "rationale": "Tests basic hash map usage for efficient lookups.",
      "score": 15
    }}
    Ensure the entire output is a valid JSON list containing exactly 5 such objects.
    """
)

INTERVIEW_GUIDE_PROMPT = PromptTemplate(
    input_variables=["parsed_input", "questions"],
    template="""
    Create a comprehensive interview guide based on:
    
    PARSED INPUT:
    {parsed_input}
    
    GENERATED QUESTIONS:
    {questions}
    
    Include:
    1. Structured sections
    2. Time allocations
    3. Scoring criteria
    4. Special notes
    5. Interviewer guidelines
    
    Return the guide in JSON format matching the InterviewGuide model structure.
    """
)