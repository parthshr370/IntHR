# Dynamic Interview Module

This module is part of a larger HR portal system that generates dynamic interview questions based on job descriptions, resumes, and online assessment results.

## Overview

The module takes the output from a previous Online Assessment (OA) module in markdown format and generates a comprehensive interview guide tailored to the candidate's profile and performance.

### Features

- Parses unstructured markdown input containing JD, resume, and OA results
- Generates dynamic interview questions across multiple categories:
  - Technical Assessment
  - Coding Challenge
  - System Design (for mid/senior levels)
  - Behavioral Assessment
- Questions are influenced by:
  - Job requirements
  - Candidate's skills and experience
  - OA performance and responses
- Provides structured interview guides with:
  - Question rationale
  - Expected answers
  - Follow-up questions
  - Scoring criteria

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables:
```bash
export REASONING_API_KEY="your-openrouter-api-key"  # For gemini-2.5-pro
export NON_REASONING_API_KEY="your-openrouter-api-key"  # For gemini-2.0-flash
```

## Usage

1. Place your OA output markdown file in the `tests` directory as `sample_input.md` (if not already present).

2. Run the test suite:
```bash
pytest tests/
```

Alternatively, to run the main processing script:

```bash
python main.py tests/sample_input.md -o output_directory
```

## Project Structure

```
.
├── agents/
│   ├── parser_agent.py     # Parses markdown input
│   └── interview_agent.py  # Generates interview guide
├── models/
│   └── data_models.py      # Pydantic models
├── utils/
│   ├── md_parser.py        # Markdown parsing utilities
│   └── logging_config.py   # Logging configuration
├── templates/
│   └── prompts.py         # LLM prompts
├── tests/
│   ├── test_parser.py     # Parser agent tests
│   └── test_interview.py  # Interview agent tests
├── requirements.txt
└── README.md
```

## Input Format

The module expects a markdown file containing:
- Job Description
- Resume (in JSON format)
- OA Results (including scores and feedback)

See `tests/sample_input.md` for an example.

## Output

The module generates:
1. Parsed structured data (saved as `parser_output.json`)
2. Complete interview guide (saved as `interview_guide.json`)

## Models Used

- Non-reasoning tasks (parsing): `google/gemini-2.0-flash-001`
- Reasoning tasks (question generation): `google/gemini-2.5-pro-preview-03-25`

Both models are accessed through the OpenRouter API. 