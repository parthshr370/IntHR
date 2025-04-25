from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime

class PersonalInfo(BaseModel):
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None

class Education(BaseModel):
    degree: str
    institution: str
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    field: Optional[str] = None
    graduation_date: Optional[str] = None

class Experience(BaseModel):
    title: str
    company: str
    duration: str
    description: List[str]
    location: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    responsibilities: List[str]
    achievements: List[str]

class Project(BaseModel):
    name: str
    description: str
    technologies: List[str]
    url: Optional[str] = None

class ResumeData(BaseModel):
    personal_info: PersonalInfo
    summary: Optional[str] = None
    education: List[Education]
    experience: List[Experience]
    skills: List[str]
    projects: List[Project]
    certifications: List[str]

class JobDescription(BaseModel):
    job_title: str
    location: str
    experience_level: str
    responsibilities: List[str] = []
    qualifications: List[str] = []
    preferred_qualifications: List[str] = []

class OAResult(BaseModel):
    total_score: int
    status: str
    technical_rating: float
    passion_rating: float
    performance_by_category: Dict[str, float]
    detailed_feedback: Dict[str, Any]

class InterviewQuestion(BaseModel):
    id: str = Field(..., description="Unique identifier for the question")
    category: str = Field(..., description="Category of the question (technical, behavioral, etc)")
    question: str = Field(..., description="The actual question text")
    expected_answer: str = Field(..., description="Expected or ideal answer")
    follow_up_questions: List[str] = Field(default_factory=list, description="Follow-up questions")
    # Change difficulty from str to int to match LLM output
    difficulty: int = Field(..., description="Difficulty level of the question (e.g., 1-5)")
    skills_tested: List[str] = Field(default_factory=list, description="Skills being tested")
    rationale: str = Field(..., description="Why this question was chosen")
    score: int = Field(..., description="Maximum score for this question")

class InterviewSection(BaseModel):
    name: str
    description: str
    questions: List[InterviewQuestion]
    total_score: int
    passing_score: int

class InterviewGuide(BaseModel):
    candidate_name: str
    job_title: str
    interview_date: datetime = Field(default_factory=datetime.now)
    sections: List[InterviewSection]
    total_score: int
    passing_score: int
    special_notes: List[str] = Field(default_factory=list)
    interviewer_guidelines: List[str] = Field(default_factory=list)

class ParsedInput(BaseModel):
    job_description: JobDescription
    resume_data: ResumeData
    oa_results: OAResult