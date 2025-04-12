# tests/test_generator.py

import pytest
import os
import asyncio
from agents.question_generator import QuestionGenerator

@pytest.fixture
def question_generator():
    """Creates a QuestionGenerator instance for testing"""
    return QuestionGenerator(os.getenv("NON_REASONING_API_KEY"))

@pytest.mark.asyncio
async def test_generate_coding_question(question_generator):
    """Test the coding question generation method"""
    skills = ["Python", "Java"]
    level = "mid"
    
    question = await question_generator._create_coding_question(skills, level)
    assert question is not None
    assert question.type == "coding"
    assert question.text is not None
    assert len(question.options) == 4
    assert isinstance(question.correct_option, int)
    assert question.correct_option >= 0 and question.correct_option <= 3
    
@pytest.mark.asyncio
async def test_generate_system_design_question(question_generator):
    """Test the system design question generation method"""
    level = "senior"
    
    question = await question_generator._create_system_design_question(level)
    assert question is not None
    assert question.type == "system_design"
    assert question.text is not None
    assert question.scenario is not None
    assert len(question.requirements) > 0
    assert len(question.expected_components) > 0
    
@pytest.mark.asyncio
async def test_generate_behavioral_question(question_generator):
    """Test the behavioral question generation method"""
    level = "mid"
    
    question = await question_generator._create_behavioral_question(level)
    assert question is not None
    assert question.type == "behavioral"
    assert question.text is not None
    assert question.context is not None
    assert len(question.evaluation_points) > 0

@pytest.mark.asyncio
async def test_generate_complete_assessment(question_generator):
    """Test end-to-end assessment generation"""
    assessment = await question_generator.generate_assessment(
        candidate_name="Test Candidate",
        job_title="Software Engineer",
        skills=["Python", "Machine Learning"],
        experience=[{"title": "Developer", "company": "Tech Co"}],
        level="mid",
        job_requirements={"required_skills": ["Python"]},
        candidate_profile={"key_skills": ["Python"]}
    )
    
    assert assessment is not None
    assert assessment.candidate_name == "Test Candidate"
    assert len(assessment.coding_questions) > 0
    assert len(assessment.system_design_questions) > 0
    assert len(assessment.behavioral_questions) > 0
    assert assessment.total_score > 0
    assert assessment.passing_score > 0

@pytest.mark.asyncio
async def test_structured_response_generation(question_generator):
    """Test the structured response generation utility"""
    template = """
    Create a test question about {topic}.
    Respond with the following fields:
    - text: The question text
    - difficulty: easy, medium, or hard
    """
    
    params = {"topic": "Python programming"}
    result = await question_generator._generate_structured_response(template, params)
    
    assert result is not None
    assert isinstance(result, dict)