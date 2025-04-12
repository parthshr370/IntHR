# utils/content_analyzer.py

import os
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)
logger.info("Initializing ContentAnalyzer")

from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
import mistune
import json
import re

class ContentAnalyzer:
    """
    Simplified content analyzer that uses AI to understand documents
    """
    
    def __init__(self, non_reasoning_api_key: str):
        self.llm = ChatOpenAI(
            model="google/gemini-2.0-flash-001",
            temperature=0.2,
            openai_api_key=non_reasoning_api_key,
            openai_api_base="https://openrouter.ai/api/v1"
        )
        
        self.markdown_parser = mistune.create_markdown()
        
        self.analysis_prompt = PromptTemplate(
            input_variables=["content"],
            template="""
            Analyze this content containing a job description, resume, and previous analysis.
            Extract the exact information as written in the document.
            
            Content:
            {content}
            
            Provide a JSON response with this exact structure:
            {{
                "job_details": {{
                    "title": "<exact title from document>",
                    "required_skills": ["<skill1>", "<skill2>", ...],
                    "experience_needed": "<exact experience requirement>",
                    "responsibilities": ["<resp1>", "<resp2>", ...],
                    "key_requirements": ["<req1>", "<req2>", ...]
                }},
                "candidate_details": {{
                    "name": "<exact name from document>",
                    "experience_level": "<junior/mid/senior>",
                    "total_years": <number>,
                    "key_skills": ["<skill1>", "<skill2>", ...],
                    "relevant_experience": [
                        {{
                            "title": "<job title>",
                            "company": "<company name>",
                            "duration": "<duration>",
                            "details": ["<detail1>", "<detail2>", ...]
                        }}
                    ],
                    "education": [
                        {{
                            "degree": "<degree>",
                            "institution": "<institution>"
                        }}
                    ]
                }},
                "previous_analysis": {{
                    "ats_score": <number between 0 and 100>,
                    "key_matches": ["<match1>", "<match2>", ...],
                    "missing_skills": ["<skill1>", "<skill2>", ...],
                    "recommendations": ["<rec1>", "<rec2>", ...]
                }},
                "skill_gap_analysis": {{
                    "matching_skills": ["<skill1>", "<skill2>", ...],
                    "missing_critical_skills": ["<skill1>", "<skill2>", ...],
                    "experience_match": <number between 0 and 1>,
                    "overall_fit": <number between 0 and 1>
                }}
            }}

            Extract EXACT values from the document where possible. Don't modify or paraphrase the original text.
            """
        )

    def _extract_sections(self, content: str) -> Dict[str, str]:
        """Extract main sections from markdown content"""
        sections = {}
        current_section = None
        lines = []
        
        for line in content.split('\n'):
            if line.startswith('# '):
                if current_section and lines:
                    sections[current_section] = '\n'.join(lines).strip()
                current_section = line[2:].strip()
                lines = []
            else:
                lines.append(line)
                
        if current_section and lines:
            sections[current_section] = '\n'.join(lines).strip()
            
        return sections

    def _extract_field(self, content: str, field: str) -> str:
        """Extract specific field from content"""
        match = re.search(rf'{field}:\s*(.+)', content)
        if match:
            return match.group(1).strip()
        return ""

    def parse_markdown(self, content: str) -> Dict[str, Any]:
        """Parse markdown content into structured data"""
        try:
            sections = self._extract_sections(content)
            
            # Extract basic information
            jd_section = sections.get('Job Description', '')
            resume_section = sections.get('Resume', '')
            
            # Parse job details
            job_title = self._extract_field(jd_section, 'Title')
            job_location = self._extract_field(jd_section, 'Location')
            job_experience = self._extract_field(jd_section, 'Experience')
            
            # Parse resume details
            candidate_name = self._extract_field(resume_section, 'Name')
            candidate_email = self._extract_field(resume_section, 'Email')
            
            return {
                "job_description": {
                    "title": job_title,
                    "location": job_location,
                    "experience": job_experience,
                    "section_content": jd_section
                },
                "resume": {
                    "name": candidate_name,
                    "email": candidate_email,
                    "section_content": resume_section
                },
                "raw_sections": sections
            }
        except Exception as e:
            print(f"Error parsing markdown: {e}")
            return {}

    async def analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content using AI"""
        try:
            # First parse the markdown structure
            parsed_data = self.parse_markdown(content)
            
            # Get AI analysis
            analysis_response = await self.llm.ainvoke(
                self.analysis_prompt.format(content=json.dumps(parsed_data, indent=2))
            )
            
            # Parse the response
            try:
                # First try to extract JSON from the response
                response_text = analysis_response.content
                # Find JSON content (anything between first { and last })
                json_content = response_text[response_text.find('{'):response_text.rfind('}')+1]
                analysis = json.loads(json_content)
            except json.JSONDecodeError:
                print("Error decoding JSON response, using parsed data")
                # Fallback to structured data from parsing
                analysis = self._create_analysis_from_parsed(parsed_data)
            
            # Validate and clean the analysis
            cleaned = self._clean_analysis(analysis, parsed_data)
            return cleaned
            
        except Exception as e:
            print(f"Error analyzing content: {e}")
            return self._get_default_structure()
    
    def _create_analysis_from_parsed(self, parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create analysis structure from parsed data"""
        return {
            "job_details": {
                "title": parsed_data.get("job_description", {}).get("title", "Software Engineer"),
                "required_skills": self._extract_skills(parsed_data.get("job_description", {}).get("section_content", "")),
                "experience_needed": parsed_data.get("job_description", {}).get("experience", "Not specified"),
                "responsibilities": [],
                "key_requirements": []
            },
            "candidate_details": {
                "name": parsed_data.get("resume", {}).get("name", "Candidate"),
                "experience_level": "mid",
                "total_years": 0.0,
                "key_skills": self._extract_skills(parsed_data.get("resume", {}).get("section_content", "")),
                "relevant_experience": [],
                "education": []
            },
            "previous_analysis": {
                "ats_score": 0.0,
                "key_matches": [],
                "missing_skills": [],
                "recommendations": []
            },
            "skill_gap_analysis": {
                "matching_skills": [],
                "missing_critical_skills": [],
                "experience_match": 0.0,
                "overall_fit": 0.0
            }
        }
    
    def _extract_skills(self, content: str) -> List[str]:
        """Extract skills from content"""
        skills = []
        for line in content.split('\n'):
            if line.strip().startswith('- '):
                skills.append(line.strip()[2:])
        return skills
    
    def _clean_analysis(self, analysis: Dict[str, Any], parsed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean and validate analysis data"""
        # Ensure correct title
        if not analysis["job_details"]["title"]:
            analysis["job_details"]["title"] = parsed_data.get("job_description", {}).get("title", "Software Engineer")
            
        # Ensure correct candidate name
        if not analysis["candidate_details"]["name"]:
            analysis["candidate_details"]["name"] = parsed_data.get("resume", {}).get("name", "Candidate")
            
        # Ensure valid experience level
        if "experience_level" not in analysis["candidate_details"]:
            analysis["candidate_details"]["experience_level"] = "mid"
            
        self._ensure_complete_structure(analysis)
        return analysis
    
    def _ensure_complete_structure(self, data: Dict[str, Any]) -> None:
        """Ensure all required fields exist"""
        default = self._get_default_structure()
        for key, value in default.items():
            if key not in data:
                data[key] = value
            elif isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    if sub_key not in data[key]:
                        data[key][sub_key] = sub_value
    
    def _get_default_structure(self) -> Dict[str, Any]:
        """Return default data structure"""
        return {
            "job_details": {
                "title": "Software Engineer",
                "required_skills": ["Programming"],
                "experience_needed": "Not specified",
                "responsibilities": [],
                "key_requirements": []
            },
            "candidate_details": {
                "name": "Candidate",
                "experience_level": "mid",
                "total_years": 0.0,
                "key_skills": [],
                "relevant_experience": [],
                "education": []
            },
            "previous_analysis": {
                "ats_score": 0.0,
                "key_matches": [],
                "missing_skills": [],
                "recommendations": []
            },
            "skill_gap_analysis": {
                "matching_skills": [],
                "missing_critical_skills": [],
                "experience_match": 0.0,
                "overall_fit": 0.0
            }
        }