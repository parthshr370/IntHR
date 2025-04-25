import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from agents.interview_agent import InterviewAgent
from models.data_models import (
    ParsedInput, JobDescription, ResumeData, OAResult, PersonalInfo, 
    InterviewGuide, InterviewQuestion
)

# --- Mock Data ---

@pytest.fixture
def mock_parsed_input():
    """Provides a reusable mock ParsedInput object."""
    return ParsedInput(
        job_description=JobDescription(
            job_title="Test Engineer", location="Test Location", experience_level="Mid",
            responsibilities=["Testing"], qualifications=["Python"], preferred_qualifications=[]
        ),
        resume_data=ResumeData(
            personal_info=PersonalInfo(name="Mock Interviewee"),
            summary="Test summary", education=[], experience=[], 
            skills=["Pytest"], projects=[], certifications=[]
        ),
        oa_results=OAResult(
            total_score=80, status="Passed", technical_rating=4.0, passion_rating=3.5,
            performance_by_category={}, detailed_feedback={}
        )
    )

# Mock LLM response (list of question dicts)
MOCK_QUESTION_LIST_JSON = json.dumps([
    {
        "question": "Explain dependency injection.",
        "expected_answer": "DI is a design pattern...",
        "follow_up_questions": ["When is it useful?"],
        "difficulty": "Medium",
        "skills_tested": ["Design Patterns", "Architecture"],
        "rationale": "Assesses understanding of core concepts.",
        "score": 10
    },
    {
        "question": "Describe a challenging project.",
        "expected_answer": "STAR method response...",
        "follow_up_questions": [],
        "difficulty": "Easy",
        "skills_tested": ["Communication", "Problem Solving"],
        "rationale": "Behavioral assessment.",
        "score": 5
    }
])

MOCK_EMPTY_RESPONSE_JSON = json.dumps([])
MOCK_INVALID_RESPONSE = "This is not json"

# --- Fixtures ---

@pytest.fixture
def interview_agent():
    """Provides an InterviewAgent instance with a dummy API key."""
    return InterviewAgent(reasoning_api_key="dummy-reasoning-key")

# --- Test Functions ---

def test_interview_agent_initialization(interview_agent):
    """Test if InterviewAgent initializes ChatOpenAI correctly."""
    assert interview_agent.llm is not None
    assert interview_agent.llm.openai_api_key.get_secret_value() == "dummy-reasoning-key"
    assert interview_agent.llm.openai_api_base == "https://openrouter.ai/api/v1"

@patch('agents.interview_agent.ChatOpenAI') # Mock the class
def test_interview_agent_initialization_mocked(MockChatOpenAI):
    """Test initialization ensures ChatOpenAI is called with correct params."""
    agent = InterviewAgent(reasoning_api_key="dummy-reasoning-key-2")
    MockChatOpenAI.assert_called_once_with(
        model="google/gemini-2.5-pro-preview-03-25",
        temperature=0.7,
        openai_api_key="dummy-reasoning-key-2",
        openai_api_base="https://openrouter.ai/api/v1",
        max_tokens=4096
    )

# --- Test _parse_questions_response ---

def test_parse_questions_response_success(interview_agent):
    """Test parsing a valid JSON list response."""
    parsed = interview_agent._parse_questions_response(f"```json\n{MOCK_QUESTION_LIST_JSON}\n```")
    assert len(parsed) == 2
    assert parsed[0]["question"] == "Explain dependency injection."
    assert parsed[1]["score"] == 5

def test_parse_questions_response_dict_format(interview_agent):
    """Test parsing a valid JSON dict response with 'questions' key."""
    response_str = json.dumps({"questions": json.loads(MOCK_QUESTION_LIST_JSON)})
    parsed = interview_agent._parse_questions_response(response_str)
    assert len(parsed) == 2
    assert parsed[0]["question"] == "Explain dependency injection."

def test_parse_questions_response_single_dict(interview_agent):
    """Test parsing a response that's just a single question dictionary."""
    single_question_json = json.dumps(json.loads(MOCK_QUESTION_LIST_JSON)[0])
    parsed = interview_agent._parse_questions_response(single_question_json)
    assert len(parsed) == 1
    assert parsed[0]["question"] == "Explain dependency injection."

def test_parse_questions_response_invalid_json(interview_agent):
    """Test parsing an invalid JSON response."""
    parsed = interview_agent._parse_questions_response(MOCK_INVALID_RESPONSE)
    assert parsed == []

def test_parse_questions_response_no_markdown(interview_agent):
    """Test parsing valid JSON without markdown fences."""
    parsed = interview_agent._parse_questions_response(MOCK_QUESTION_LIST_JSON)
    assert len(parsed) == 2
    assert parsed[0]["question"] == "Explain dependency injection."

# --- Test _generate_*_questions (Async) ---

@pytest.mark.asyncio
@patch('agents.interview_agent.ChatOpenAI', new_callable=MagicMock)
async def test_generate_technical_questions(MockChatOpenAI, mock_parsed_input):
    """Test _generate_technical_questions with mocked LLM."""
    mock_llm_instance = MockChatOpenAI.return_value
    mock_response = MagicMock()
    mock_response.content = MOCK_QUESTION_LIST_JSON
    mock_llm_instance.invoke = AsyncMock(return_value=mock_response) # Make the instance's invoke async

    agent = InterviewAgent(reasoning_api_key="dummy-reasoning-key")

    assert agent.llm is mock_llm_instance # Verify agent uses mock

    questions = await agent._generate_technical_questions(mock_parsed_input)

    mock_llm_instance.invoke.assert_awaited_once() # Check if awaited on the instance
    assert len(questions) == 2
    assert isinstance(questions[0], InterviewQuestion)
    assert questions[0].category == "technical"
    assert questions[0].question == "Explain dependency injection."
    assert questions[1].category == "technical"
    assert questions[1].score == 5

# Similar async tests would be written for:
# _generate_behavioral_questions
# _generate_system_design_questions
# _generate_coding_questions
# (Skipping for brevity, but structure is identical to test_generate_technical_questions)

@pytest.mark.asyncio
@patch('agents.interview_agent.ChatOpenAI', new_callable=MagicMock)
async def test_generate_questions_llm_error(MockChatOpenAI, mock_parsed_input):
    """Test question generation when LLM invoke raises an error."""
    mock_llm_instance = MockChatOpenAI.return_value
    mock_llm_instance.invoke = AsyncMock(side_effect=Exception("LLM API Error"))

    agent = InterviewAgent(reasoning_api_key="dummy-reasoning-key")

    assert agent.llm is mock_llm_instance # Verify agent uses mock

    questions = await agent._generate_technical_questions(mock_parsed_input)

    mock_llm_instance.invoke.assert_awaited_once()
    assert questions == [] # Expect empty list on error

# --- Test generate_interview_guide (Async) ---

@pytest.mark.asyncio
@patch('agents.interview_agent.InterviewAgent._generate_technical_questions', new_callable=AsyncMock)
@patch('agents.interview_agent.InterviewAgent._generate_coding_questions', new_callable=AsyncMock)
@patch('agents.interview_agent.InterviewAgent._generate_system_design_questions', new_callable=AsyncMock)
@patch('agents.interview_agent.InterviewAgent._generate_behavioral_questions', new_callable=AsyncMock)
async def test_generate_interview_guide_mid_level(
    mock_gen_behavioral, mock_gen_design, mock_gen_coding, mock_gen_tech,
    interview_agent, mock_parsed_input
):
    """Test generate_interview_guide for a mid-level role."""
    # Prepare mock questions for each section
    tech_q = [InterviewQuestion(id='t1', category='technical', question='T1?', expected_answer='TA1', difficulty='M', rationale='R', score=10)]
    code_q = [InterviewQuestion(id='c1', category='coding', question='C1?', expected_answer='CA1', difficulty='M', rationale='R', score=15)]
    design_q = [InterviewQuestion(id='d1', category='system_design', question='D1?', expected_answer='DA1', difficulty='H', rationale='R', score=20)]
    behav_q = [InterviewQuestion(id='b1', category='behavioral', question='B1?', expected_answer='BA1', difficulty='E', rationale='R', score=5)]
    
    mock_gen_tech.return_value = tech_q
    mock_gen_coding.return_value = code_q
    mock_gen_design.return_value = design_q # Should be called for mid-level
    mock_gen_behavioral.return_value = behav_q

    guide = await interview_agent.generate_interview_guide(mock_parsed_input)
    
    mock_gen_tech.assert_awaited_once_with(mock_parsed_input)
    mock_gen_coding.assert_awaited_once_with(mock_parsed_input)
    mock_gen_design.assert_awaited_once_with(mock_parsed_input)
    mock_gen_behavioral.assert_awaited_once_with(mock_parsed_input)
    
    assert isinstance(guide, InterviewGuide)
    assert guide.candidate_name == "Mock Interviewee"
    assert guide.job_title == "Test Engineer"
    assert len(guide.sections) == 4 # Tech, Coding, Design, Behavioral
    assert guide.sections[0].name == "Technical Assessment"
    assert guide.sections[0].questions == tech_q
    assert guide.sections[1].name == "Coding Challenge"
    assert guide.sections[1].questions == code_q
    assert guide.sections[2].name == "System Design"
    assert guide.sections[2].questions == design_q
    assert guide.sections[3].name == "Behavioral Assessment"
    assert guide.sections[3].questions == behav_q
    assert guide.total_score == (10 + 15 + 20 + 5)
    assert guide.passing_score == int(10 * 0.7) + int(15 * 0.7) + int(20 * 0.7) + int(5 * 0.7)

@pytest.mark.asyncio
@patch('agents.interview_agent.InterviewAgent._generate_technical_questions', new_callable=AsyncMock)
@patch('agents.interview_agent.InterviewAgent._generate_coding_questions', new_callable=AsyncMock)
@patch('agents.interview_agent.InterviewAgent._generate_system_design_questions', new_callable=AsyncMock)
@patch('agents.interview_agent.InterviewAgent._generate_behavioral_questions', new_callable=AsyncMock)
async def test_generate_interview_guide_junior_level(
    mock_gen_behavioral, mock_gen_design, mock_gen_coding, mock_gen_tech,
    interview_agent, mock_parsed_input
):
    """Test generate_interview_guide for a junior-level role (no system design)."""
    # Change experience level for this test
    mock_parsed_input.job_description.experience_level = "Junior"
    
    tech_q = [InterviewQuestion(id='t1', category='technical', question='T1?', expected_answer='TA1', difficulty='M', rationale='R', score=10)]
    code_q = [InterviewQuestion(id='c1', category='coding', question='C1?', expected_answer='CA1', difficulty='M', rationale='R', score=15)]
    behav_q = [InterviewQuestion(id='b1', category='behavioral', question='B1?', expected_answer='BA1', difficulty='E', rationale='R', score=5)]
    
    mock_gen_tech.return_value = tech_q
    mock_gen_coding.return_value = code_q
    # Design questions mock is present but should NOT be called
    mock_gen_behavioral.return_value = behav_q

    guide = await interview_agent.generate_interview_guide(mock_parsed_input)
    
    mock_gen_tech.assert_awaited_once_with(mock_parsed_input)
    mock_gen_coding.assert_awaited_once_with(mock_parsed_input)
    mock_gen_design.assert_not_awaited() # System design should NOT be called
    mock_gen_behavioral.assert_awaited_once_with(mock_parsed_input)
    
    assert len(guide.sections) == 3 # Tech, Coding, Behavioral (no design)
    assert guide.sections[0].name == "Technical Assessment"
    assert guide.sections[1].name == "Coding Challenge"
    assert guide.sections[2].name == "Behavioral Assessment"
    assert guide.total_score == (10 + 15 + 5)
