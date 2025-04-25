# Integrated HR Recruitment System

A comprehensive HR recruitment pipeline consisting of four specialized modules that work together to streamline and enhance the entire recruitment process, from job posting to interview management.

## System Overview

This integrated system automates and optimizes the entire recruitment workflow through four key modules:

1. **Job Description Generator (JD)**: Creates professional, AI-generated job descriptions and publishes them across platforms.
2. **Applicant Tracking System (ATS)**: Parses resumes, matches candidates against job requirements, and provides detailed hiring recommendations.
3. **Online Assessment Module (OA)**: Generates personalized technical assessments based on job descriptions and candidate profiles.
4. **Dynamic Interview Module**: Creates tailored interview questions and structured interview guides based on previous stages.

## Project Structure

```
.
├── JD Final/             # Job Description Generator & Publisher
├── ATS Final/            # Applicant Tracking System
├── OA_Final/             # Online Assessment Module
├── Interview Final/      # Dynamic Interview Module
└── .gitignore            # Git ignore configuration
```

## Module Details

### Job Description Generator

Creates professional, detailed job descriptions using AI (Gemini or OpenAI), with posting capabilities for various job platforms.

**Key Features:**
- Multi-step form for job requirement collection
- AI-powered generation of natural job descriptions
- Job posting capabilities for multiple platforms
- Export options in Markdown and HTML

### Applicant Tracking System (ATS)

Parses resumes, matches them against job descriptions, and provides hiring recommendations.

**Key Features:**
- Resume parsing with structured output
- Job requirement matching with detailed analysis
- Hiring decision recommendations
- Support for multiple file formats (PDF, DOCX, TXT)

### Online Assessment Module (OA)

Generates personalized assessments based on job descriptions and candidate resumes.

**Key Features:**
- Dynamic question generation based on JD-resume matches
- Multiple question types (coding, system design, behavioral)
- Automated evaluation with detailed feedback
- Passion detection in responses

### Dynamic Interview Module

Creates comprehensive interview guides tailored to candidates' profiles and performance.

**Key Features:**
- Parses unstructured markdown from previous modules
- Generates questions across multiple categories
- Provides structured interview guides with rationale
- Creates follow-up questions and scoring criteria

## Setup Instructions

Each module has its own setup instructions. Please refer to the README.md file in each module directory for detailed setup and usage information.

## General Requirements

- Python 3.8 or higher
- API keys for chosen LLM providers (OpenAI, Google Gemini, or OpenRouter)
- Necessary dependencies listed in each module's requirements.txt

## Technology Stack

- **Frontend**: Streamlit for web interfaces
- **Backend**: Python-based microservices
- **AI/ML**: Integration with OpenAI, Google Gemini, and OpenRouter
- **Document Processing**: PDF, DOCX, and TXT parsing capabilities
- **APIs**: Integration with job boards and notification services

## License

This project is proprietary software. All rights reserved.

## Authors

Udayan Pawar