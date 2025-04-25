import pytest
import json
import sys
import os
from unittest.mock import patch, MagicMock

# Add project root to sys.path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)

from agents.parser_agent import ParserAgent
from models.data_models import ParsedInput

# Sample Markdown for testing
SAMPLE_MARKDOWN = """
# Job Description
## Title: Software Engineer
## Location: Remote
## Experience: Mid-level
* Responsibility 1
* Qualification 1

# Resume
## Name: Test Candidate
## Summary: Experienced developer.
* Skill 1

# OA Results
## Score: 85
## Status: Passed
```json
{
  "some_json": "data"
}
```
"""

# Mock LLM response for successful parsing
MOCK_LLM_RESPONSE_SUCCESS = json.dumps({
    "job_description": {
        "job_title": "Senior Test Engineer",
        "location": "Test City",
        "experience_level": "Senior",
        "responsibilities": ["Testing frameworks"],
        "qualifications": ["Pytest", "Mocking"],
        "preferred_qualifications": ["CI/CD"]
    },
    "resume_data": {
        "personal_info": {"name": "Mock Candidate"},
        "summary": "A mock summary.",
        "education": [],
        "experience": [],
        "skills": ["Python", "Testing"],
        "projects": [],
        "certifications": []
    },
    "oa_results": {
        "total_score": 90,
        "status": "Strong Pass",
        "technical_rating": 4.5,
        "passion_rating": 4.0,
        "performance_by_category": {"coding": 0.9},
        "detailed_feedback": {"strengths": "Good logic"}
    }
})

# Mock LLM response that causes JSON decode error
MOCK_LLM_RESPONSE_INVALID_JSON = "This is not valid JSON { maybe"

@pytest.fixture
def parser_agent():
    """Provides a ParserAgent instance with a dummy API key."""
    return ParserAgent(non_reasoning_api_key="dummy-key")

# --- Test Functions ---

def test_parser_agent_initialization(parser_agent):
    """Test if ParserAgent initializes ChatOpenAI correctly."""
    assert parser_agent.llm is not None
    # Use get_secret_value() for comparison
    assert parser_agent.llm.openai_api_key.get_secret_value() == "dummy-key"
    assert parser_agent.llm.openai_api_base == "https://openrouter.ai/api/v1"

@patch('agents.parser_agent.ChatOpenAI') # Mock the class used for instantiation
def test_parser_agent_initialization_mocked(MockChatOpenAI):
    """Test initialization ensures ChatOpenAI is called with correct params."""
    agent = ParserAgent(non_reasoning_api_key="dummy-key-2")
    MockChatOpenAI.assert_called_once_with(
        model="google/gemini-2.0-flash-001",
        temperature=0.2,
        openai_api_key="dummy-key-2",
        openai_api_base="https://openrouter.ai/api/v1",
        max_tokens=4096
    )

@patch('utils.md_parser.MarkdownParser.extract_raw_text')
@patch('agents.parser_agent.ChatOpenAI', new_callable=MagicMock)
def test_parse_markdown_success(MockChatOpenAI, mock_extract_raw_text):
    """Test successful parsing of markdown content."""
    # Configure mocks
    mock_extract_raw_text.return_value = "Extracted raw text"

    # Configure the mock LLM *instance*
    mock_llm_instance = MockChatOpenAI.return_value
    mock_llm_response = MagicMock()
    mock_llm_response.content = MOCK_LLM_RESPONSE_SUCCESS
    mock_llm_instance.invoke.return_value = mock_llm_response

    # Instantiate agent *inside* the test
    agent = ParserAgent(non_reasoning_api_key="dummy-key")

    # Verify agent uses the mock instance
    assert agent.llm is mock_llm_instance

    # Call the method
    parsed_input = agent.parse_markdown(SAMPLE_MARKDOWN)

    # Assertions
    mock_extract_raw_text.assert_called_once_with(SAMPLE_MARKDOWN)
    mock_llm_instance.invoke.assert_called_once()
    # Check the type and some key data points
    assert isinstance(parsed_input, ParsedInput)
    assert parsed_input.job_description.job_title == "Senior Test Engineer"
    # Corrected: Use attribute access for Pydantic model field
    assert parsed_input.resume_data.personal_info.name == "Mock Candidate" 
    # Corrected: Assert experience is an empty list based on mock data
    assert parsed_input.resume_data.experience == []
    assert parsed_input.resume_data.skills == ["Python", "Testing"]
    assert parsed_input.oa_results.total_score == 90
    assert parsed_input.oa_results.status == "Strong Pass"

@patch('utils.md_parser.MarkdownParser.extract_raw_text')
@patch('agents.parser_agent.ChatOpenAI', new_callable=MagicMock)
def test_parse_markdown_json_error(MockChatOpenAI, mock_extract_raw_text):
    """Test handling of invalid JSON response from LLM."""
    # Configure mocks
    mock_extract_raw_text.return_value = "Extracted raw text"
    mock_llm_instance = MockChatOpenAI.return_value
    mock_llm_response = MagicMock()
    mock_llm_response.content = MOCK_LLM_RESPONSE_INVALID_JSON
    mock_llm_instance.invoke.return_value = mock_llm_response

    # Instantiate agent *inside* the test
    agent = ParserAgent(non_reasoning_api_key="dummy-key")

    assert agent.llm is mock_llm_instance # Verify agent uses mock

    # Call the method and expect an exception
    with pytest.raises(json.JSONDecodeError):
        agent.parse_markdown(SAMPLE_MARKDOWN)

    # Assertions
    mock_extract_raw_text.assert_called_once_with(SAMPLE_MARKDOWN)
    mock_llm_instance.invoke.assert_called_once()
