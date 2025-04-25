# Form templates for the UI

STEP1_FIELDS = [
    {
        "key": "company_name", 
        "label": "Company Name:", 
        "type": "text",
        "required": True
    },
    {
        "key": "cultural_fit_factors", 
        "label": "Cultural Fit Factors:", 
        "type": "multiselect", 
        "options": ["Customer Centricity", "Leadership", "Integrity", "Collaboration", 
                   "Adaptability", "Innovation", "Excellence", "Transparency"],
        "required": True
    },
    {
        "key": "personality_traits", 
        "label": "Personality Traits:", 
        "type": "multiselect",
        "options": ["Analytical", "Team Player", "Proactive", "Communication", 
                   "Problem Solving", "Detail-Oriented", "Creative", "Self-Motivated"],
        "required": True
    }
]

STEP2_FIELDS = [
    {
        "key": "work_experience", 
        "label": "Work Experience:", 
        "type": "text",
        "required": True
    },
    {
        "key": "technology_domain", 
        "label": "Technology/Domain:", 
        "type": "multiselect",
        "options": ["Python", "Java", "React", "UI/UX", "Sales", "Marketing", 
                   "Product Manager", "Data Science", "DevOps", "Cloud"],
        "required": True
    },
    {
        "key": "tools", 
        "label": "Tools:", 
        "type": "multiselect",
        "options": ["Pytorch/tensorflow", "JIRA", "Kubernetes", "MS Office", "Salesforce", 
                   "Docker", "Power BI", "AWS", "Azure", "Flask API"],
        "required": True
    }
]

STEP3_FIELDS = [
    {
        "key": "role_title", 
        "label": "Role Title:", 
        "type": "text",
        "required": True
    },
    {
        "key": "core_responsibilities", 
        "label": "Core Responsibilities:", 
        "type": "textarea",
        "required": True
    },
    {
        "key": "skills_competencies", 
        "label": "Skills & Competencies:", 
        "type": "textarea",
        "required": True
    },
    {
        "key": "education_requirements", 
        "label": "Education Requirements:", 
        "type": "text",
        "required": True
    }
]

STEP4_FIELDS = [
    {
        "key": "specialized_role_focus", 
        "label": "Specialized Role Focus:", 
        "type": "select",
        "options": ["Machine Learning Engineer", "UX Researcher", "Product Designer", "Langchain Dev", 
                   "Backend Developer", "Full Stack Developer", "Project Manager", 
                   "Machine Learning Research Scientist", "SAP architect", "Sales Representative"],
        "required": True
    },
    {
        "key": "unique_skills", 
        "label": "Unique Skills (Optional):", 
        "type": "text",
        "required": False
    },
    {
        "key": "key_deliverables", 
        "label": "Key Deliverables (Optional):", 
        "type": "text",
        "required": False
    },
    {
        "key": "location", 
        "label": "Location:", 
        "type": "text", 
        "default": "Remote | Hybrid",
        "required": True
    },
    {
        "key": "employment_type", 
        "label": "Employment Type:", 
        "type": "select", 
        "options": ["Full-Time", "Part-Time", "Contract", "Freelance"],
        "default": "Full-Time",
        "required": True
    }
]

# Combine all fields for validation purposes
ALL_FIELDS = STEP1_FIELDS + STEP2_FIELDS + STEP3_FIELDS + STEP4_FIELDS
