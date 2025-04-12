# tests/test_integration.py

import pytest
import asyncio
from pathlib import Path
from main import OAModule

@pytest.fixture
def sample_markdown():
    return """
# Job Description
Title: Senior Software Engineer
Location: Remote
Experience: 5+ years

Requirements:
- Strong Python programming skills
- Experience with distributed systems
- Knowledge of cloud architecture
- Leadership experience

# Resume
Name: John Doe
Email: john@example.com

Summary:
Experienced software engineer with 7 years of experience building scalable systems.

Skills:
- Python, Go, Java
- AWS, GCP
- Kubernetes, Docker
- System Design
- Team Leadership

Experience:
- Senior Developer at Tech Corp (4 years)
  - Led team of 5 developers
  - Designed and implemented microservices architecture
  - Reduced system latency by 40%
  
- Software Engineer at StartUp Inc (3 years)
  - Full-stack development
  - Implemented CI/CD pipeline
  - Built scalable data processing system

Education:
- MS Computer Science, Tech University
- BS Computer Engineering, Engineering College

# Previous Analysis
ATS Score: 85%
Key Matches:
- Python programming
- System architecture
- Leadership experience
- Cloud platforms

Missing Skills:
- Specific cloud certification
- GraphQL experience

Recommendations:
- Strong technical fit
- Consider system design focus
- Evaluate team leadership
"""

@pytest.fixture
def sample_responses():
    return {
        "code_1": 1,  # Index of the selected option for coding question
        "design_1": """
        For this system design, I would propose:
        1. Load balancer for traffic distribution
        2. Containerized microservices using Kubernetes
        3. Redis cache layer for performance
        4. Postgres database with read replicas
        5. CDN for static content
        6. Message queue for async processing
        
        Key considerations:
        - High availability through redundancy
        - Horizontal scalability
        - Data consistency and backup
        - Monitoring and alerting
        """,
        "behavior_1": """
        In my role at Tech Corp, I led a critical project to refactor our monolithic 
        application into microservices. The main challenge was ensuring zero downtime 
        during the migration while maintaining data consistency.

        I approached this by:
        1. Creating a detailed migration plan
        2. Implementing feature flags for gradual rollout
        3. Setting up comprehensive monitoring
        4. Leading weekly team sync meetings
        
        The result was a successful migration with:
        - 40% reduction in system latency
        - 99.99% uptime maintained
        - Improved team velocity
        - Better system scalability
        
        This experience taught me the importance of careful planning, clear communication,
        and maintaining focus on both technical and team aspects of large projects.
        """
    }

@pytest.mark.asyncio
async def test_end_to_end_flow(sample_markdown, sample_responses):
    """Test the complete assessment flow"""
    try:
        # Initialize module
        module = OAModule()
        
        # Generate assessment
        assessment = await module.process_input(sample_markdown)
        
        # Verify assessment structure
        assert assessment is not None
        assert assessment.candidate_name == "John Doe"
        assert assessment.job_title == "Senior Software Engineer"
        assert assessment.experience_level == "senior"
        
        # Verify questions were generated
        assert len(assessment.coding_questions) > 0
        assert len(assessment.system_design_questions) > 0
        assert len(assessment.behavioral_questions) > 0
        
        # Test response evaluation
        result = await module.evaluate_responses(assessment, sample_responses)
        
        # Verify result structure
        assert result is not None
        assert result.assessment_id == assessment.id
        assert result.candidate_name == "John Doe"
        assert isinstance(result.score, (int, float))
        assert isinstance(result.technical_rating, float)
        assert isinstance(result.passion_rating, float)
        
        # Verify scores and ratings are within expected ranges
        assert 0 <= result.score <= 100
        assert 0 <= result.technical_rating <= 1
        assert 0 <= result.passion_rating <= 1
        
        # Generate and verify report
        report = module.generate_report(result)
        assert report is not None
        assert isinstance(report, str)
        assert "Assessment Summary" in report
        assert "John Doe" in report
        
    except Exception as e:
        pytest.fail(f"Test failed with error: {str(e)}")

@pytest.mark.asyncio
async def test_content_analysis(sample_markdown):
    """Test the content analysis functionality"""
    module = OAModule()
    
    # Test content analyzer
    analysis = await module.analyzer.analyze_content(sample_markdown)
    
    # Verify analysis structure
    assert "job_details" in analysis
    assert "candidate_details" in analysis
    assert "previous_analysis" in analysis
    assert "skill_gap_analysis" in analysis
    
    # Verify job details
    job = analysis["job_details"]
    assert job["title"] == "Senior Software Engineer"
    assert "Python" in job["required_skills"]
    
    # Verify candidate details
    candidate = analysis["candidate_details"]
    assert candidate["name"] == "John Doe"
    assert candidate["experience_level"] == "senior"
    assert candidate["total_years"] == 7.0
    
    # Verify skill analysis
    skills = analysis["skill_gap_analysis"]
    assert len(skills["matching_skills"]) > 0
    assert isinstance(skills["experience_match"], float)
    assert 0 <= skills["experience_match"] <= 1

@pytest.mark.asyncio
async def test_question_generation():
    """Test question generation functionality"""
    module = OAModule()
    
    # Test data
    test_data = {
        "candidate_name": "John Doe",
        "job_title": "Senior Software Engineer",
        "skills": ["Python", "System Design", "Cloud Architecture"],
        "experience": [
            {
                "title": "Senior Developer",
                "duration": "4 years",
                "responsibilities": ["Team Leadership", "System Architecture"]
            }
        ],
        "level": "senior",
        "job_requirements": {
            "title": "Senior Software Engineer",
            "required_skills": ["Python", "Cloud", "Leadership"]
        },
        "candidate_profile": {
            "name": "John Doe",
            "experience_level": "senior",
            "key_skills": ["Python", "AWS", "Leadership"]
        }
    }
    
    # Generate assessment
    assessment = await module.generator.generate_assessment(**test_data)
    
    # Verify assessment structure
    assert assessment is not None
    assert assessment.candidate_name == "John Doe"
    assert assessment.job_title == "Senior Software Engineer"
    assert assessment.experience_level == "senior"
    
    # Verify question counts match configuration
    assert len(assessment.coding_questions) == 4  # senior level count
    assert len(assessment.system_design_questions) == 3  # senior level count
    assert len(assessment.behavioral_questions) == 3  # senior level count
    
    # Verify question properties
    for question in assessment.coding_questions:
        assert question.id.startswith("code_")
        assert isinstance(question.score, int)
        assert question.difficulty in ["easy", "medium", "hard"]
    
    for question in assessment.system_design_questions:
        assert question.id.startswith("design_")
        assert isinstance(question.score, int)
        assert len(question.requirements) > 0
        assert len(question.evaluation_criteria) > 0
    
    for question in assessment.behavioral_questions:
        assert question.id.startswith("behavior_")
        assert isinstance(question.score, int)
        assert len(question.evaluation_points) > 0
        assert len(question.passion_indicators) > 0

if __name__ == "__main__":
    pytest.main([__file__, "-v"])