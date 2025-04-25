from typing import List, Dict, Optional
from pydantic import BaseModel, Field
from templates.jd_template import JD_TEMPLATE, format_list_items, format_tech_tools
from config.settings import OPENAI_API_KEY, GEMINI_API_KEY, LLM_PROVIDER, LLM_MODEL, LLM_TEMPERATURE
import logging

logger = logging.getLogger(__name__)

class JobInput(BaseModel):
    """Input schema for job description generation"""
    company_name: str = Field(..., description="Name of the company")
    cultural_fit_factors: List[str] = Field(..., description="List of cultural fit factors")
    personality_traits: List[str] = Field(..., description="List of desired personality traits")
    work_experience: str = Field(..., description="Required work experience")
    technology_domain: List[str] = Field(..., description="List of technology or domain areas")
    tools: List[str] = Field(..., description="List of tools required")
    role_title: str = Field(..., description="Title of the role")
    core_responsibilities: str = Field(..., description="Core responsibilities of the role")
    skills_competencies: str = Field(..., description="Required skills and competencies")
    education_requirements: str = Field(..., description="Education requirements")
    specialized_role_focus: str = Field(..., description="Specialized focus of the role")
    unique_skills: Optional[str] = Field(None, description="Unique skills if applicable")
    key_deliverables: Optional[str] = Field(None, description="Key deliverables if applicable")
    location: str = Field("Remote | Hybrid", description="Job location")
    employment_type: str = Field("Full-Time", description="Employment type")

class JDGenerator:
    """Agent for generating job descriptions based on input data"""
    
    def __init__(self):
        self.provider = LLM_PROVIDER.lower()
        self.model = LLM_MODEL
        self.temperature = LLM_TEMPERATURE
        
        # Initialize the appropriate API client
        if self.provider == "openai":
            self._init_openai()
        elif self.provider == "gemini":
            self._init_gemini()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    def _init_openai(self):
        """Initialize OpenAI client"""
        try:
            import openai
            self.client = openai.OpenAI(api_key=OPENAI_API_KEY)
            logger.info("OpenAI client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
    def _init_gemini(self):
        """Initialize Gemini client"""
        try:
            import google.generativeai as genai
            genai.configure(api_key=GEMINI_API_KEY)
            self.client = genai
            
            # Initialize the model
            generation_config = {
                "temperature": self.temperature,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 2048,
            }
            
            self.gemini_model = self.client.GenerativeModel(
                model_name=self.model,
                generation_config=generation_config
            )
            logger.info("Gemini client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def _get_completion(self, prompt: str) -> str:
        """Get completion based on the configured provider"""
        try:
            if self.provider == "openai":
                return self._get_openai_completion(prompt)
            elif self.provider == "gemini":
                return self._get_gemini_completion(prompt)
            else:
                raise ValueError(f"Unsupported LLM provider: {self.provider}")
        except Exception as e:
            logger.error(f"Error getting completion: {e}")
            return f"Error generating content. Please check your API key and configuration. Error: {str(e)}"
    
    def _get_openai_completion(self, prompt: str) -> str:
        """Get completion from OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
    
    def _get_gemini_completion(self, prompt: str) -> str:
        """Get completion from Gemini API"""
        try:
            response = self.gemini_model.generate_content(prompt)
            
            # Handle potential blocking
            if response.candidates and response.candidates[0].content.parts:
                return response.candidates[0].content.parts[0].text
            else:
                logger.warning("Gemini response was blocked or empty")
                return "The AI model didn't generate a response for this prompt. Please try different wording."
        except Exception as e:
            logger.error(f"Gemini API error: {e}")
            raise
    
    def generate_jd(self, job_input: JobInput) -> str:
        """Generate a complete job description from input data"""
        
        # Generate the company introduction paragraph
        company_intro_prompt = f"""
        Write a compelling and crisp and short'About the Company' section for {job_input.company_name}. 
        Focus on creating a narrative that conveys these company values: {', '.join(job_input.cultural_fit_factors)}.
        Make it engaging, professional, and inspirational. Write 2-3 paragraphs that would convince top talent to join.
        Include a brief mention of the company's mission and impact.
        """
        company_intro = self._get_completion(company_intro_prompt)
        
        # Generate role overview
        role_overview_prompt = f"""
        Create a crisp and short'Role Overview' section for a {job_input.role_title} position.
        The role focuses on {job_input.specialized_role_focus} and requires {job_input.work_experience} of experience.
        The ideal candidate should have these personality traits: {', '.join(job_input.personality_traits)}.
        Write 1-2 engaging paragraphs that outline the purpose of the role, its impact on the company, 
        and what success looks like. Focus on how this role contributes to the company's mission.
        Make sure to not use placeholders like this - [] this is production level so we cannot risk giving examples.
        Just use your own brain and just Generate the best JD possible
        """
        role_overview = self._get_completion(role_overview_prompt)
        
        # Generate detailed responsibilities section
        responsibilities_prompt = f"""
        Create a comprehensive 'Key Responsibilities' section for a {job_input.role_title} position.
        Base this on the following core responsibilities: {job_input.core_responsibilities}
        
        Additional specific deliverables include: {job_input.key_deliverables if job_input.key_deliverables else "Not specified"}
        
        Transform these points into a well-structured list of 7-10  crisp and short responsibilities.
        Each responsibility should be actionable, specific, and give candidates a clear picture of the day-to-day work.
        Format as bullet points with complete sentences. Make them sound natural and comprehensive.
        """
        responsibilities = self._get_completion(responsibilities_prompt)
        
        # Generate qualifications section
        qualifications_prompt = f"""
        Create a crisp and short 'Qualifications & Skills' section for a {job_input.role_title} position.
        Required education: {job_input.education_requirements}
        Required experience: {job_input.work_experience}
        Key skills needed: {job_input.skills_competencies}
        Unique skills that set candidates apart: {job_input.unique_skills if job_input.unique_skills else "Not specified"}
        
        Format this as a well-structured section with clear subsections for:
        1. Education and experience requirements
        2. Technical skills required
        3. Soft skills required (based on these personality traits: {', '.join(job_input.personality_traits)})
        
        Make it detailed but achievable - avoid creating an impossible "unicorn" candidate description.
        """
        qualifications = self._get_completion(qualifications_prompt)
        
        # Generate benefits section
        benefits_prompt = f"""
        Create an attractive 'What We Offer' section for a job posting at {job_input.company_name}.
        Base this on these company values: {', '.join(job_input.cultural_fit_factors)}
        Employment type: {job_input.employment_type}
        Location: {job_input.location}
        
        Write 4-6 compelling bullet points that highlight the benefits of working for this company.
        Include aspects like growth opportunities, work environment, company culture, and any perks.
        Make it persuasive and aligned with what top talent in the {job_input.specialized_role_focus} field would value.
        """
        benefits = self._get_completion(benefits_prompt)
        
        # Generate tech environment section
        tech_environment_prompt = f"""
        Create a crisp and short'Technical Environment' section for this job posting.
        The role works with these technologies: {', '.join(job_input.technology_domain)}
        The team uses these tools: {', '.join(job_input.tools)}
        
        Write a paragraph that gives candidates insight into the technical stack, development practices, 
        and technical culture at the company. Mention how these technologies are used to solve problems.
        Make it detailed and authentic - avoid generic descriptions.
        """
        tech_environment = self._get_completion(tech_environment_prompt)
        
        # Fill the template
        job_description = JD_TEMPLATE.substitute(
            role_title=job_input.role_title,
            location=job_input.location,
            employment_type=job_input.employment_type,
            company_intro=company_intro,
            role_overview=role_overview,
            responsibilities=responsibilities,
            qualifications=qualifications,
            benefits=benefits,
            tech_environment=tech_environment
        )
        
        return job_description.strip()