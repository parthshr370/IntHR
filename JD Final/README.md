# Job Description Generator & Poster

## Project Overview

The Job Description Generator & Poster is an AI-powered application that creates professional, detailed job descriptions based on user inputs and can post them to various job platforms. The system uses either Google's Gemini or OpenAI's GPT models to transform simple form inputs into comprehensive, naturally-flowing job postings that attract top talent.

**Key Features:**
- Multi-step form interface for detailed job requirement collection
- AI-powered generation of natural, professional job descriptions
- Customizable job posting sections and structure
- Support for multiple AI providers (Gemini and OpenAI)
- Job posting capability for multiple platforms (Twitter, Google Jobs, etc.)
- Preview mode for testing without actually posting
- Export options (Markdown and HTML)

![System Workflow](https://via.placeholder.com/800x400?text=System+Workflow+Diagram)

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [File Structure](#file-structure)
3. [Setup and Installation](#setup-and-installation)
4. [Configuration Guide](#configuration-guide)
5. [Usage Instructions](#usage-instructions)
6. [Customization Guide](#customization-guide)
7. [API Integration](#api-integration)
8. [Troubleshooting](#troubleshooting)
9. [Future Enhancements](#future-enhancements)

## Architecture Overview

The system follows a modular architecture:

1. **User Interface Layer**: Streamlit-powered interface for collecting job details
2. **Generator Layer**: AI integration for transforming inputs into detailed job descriptions
3. **Posting Layer**: Platform connectors for distributing job postings
4. **Configuration Layer**: Settings management for API keys and preferences

The application follows this workflow:
1. Collect user inputs through a multi-step form
2. Validate inputs for completeness and correctness
3. Generate a comprehensive job description using AI
4. Preview or post the job description to selected platforms
5. Provide export options for the generated content

## File Structure

Here's a breakdown of the project's file structure and what each component does:

```
job_description_generator/
├── app.py                  # Main Streamlit application entry point
├── simplified_cli.py       # Command line interface for the generator
├── config/
│   ├── __init__.py
│   └── settings.py         # Configuration settings and API key management
├── agents/
│   ├── __init__.py
│   ├── jd_generator.py     # AI-powered job description generator
│   └── job_poster.py       # Platform posting agent
├── chains/
│   ├── __init__.py
│   └── workflow.py         # Main workflow orchestration
├── templates/
│   ├── __init__.py
│   ├── jd_template.py      # Job description template structure
│   └── form_template.py    # Form field definitions and options
├── utils/
│   ├── __init__.py
│   ├── api_connector.py    # API connection utilities
│   └── validators.py       # Input validation utilities
├── .env                    # Environment variables storage (not in git)
├── .env.template           # Template for required environment variables
├── example_input.json      # Example input for testing
├── requirements.txt        # Project dependencies
└── README.md               # Basic project information
```

### Key File Details

#### Core Files

- **app.py**: The main Streamlit web application that provides the user interface for creating job descriptions. It handles the multi-step form process, displays the generated job description, and manages job posting.

- **simplified_cli.py**: A command-line interface for generating job descriptions without the Streamlit UI. Useful for testing or batch processing.

- **chains/workflow.py**: Orchestrates the entire job generation and posting process. Manages the flow from input validation to job description generation to platform posting.

#### Configuration

- **config/settings.py**: Centralizes all configuration settings, including API keys, LLM settings, and platform configurations. Loads settings from environment variables.

- **.env.template**: Template showing all required environment variables. Users should copy this to `.env` and fill in their API keys.

#### Agents

- **agents/jd_generator.py**: Contains the `JDGenerator` class that transforms user inputs into comprehensive job descriptions using AI. Supports both OpenAI and Gemini models.

- **agents/job_poster.py**: Contains the `JobPoster` class that handles posting to various job platforms (Twitter, Google Jobs, etc.). Manages platform-specific formatting and API connections.

#### Templates

- **templates/jd_template.py**: Defines the structure and format of generated job descriptions. Contains the main template and formatting utilities.

- **templates/form_template.py**: Defines all form fields, their types, options, and validation requirements. This is where dropdown options are configured.

#### Utilities

- **utils/validators.py**: Contains validation logic for user inputs. Ensures all required fields are present and valid.

- **utils/api_connector.py**: Utilities for making API requests to external services with proper error handling.

## Setup and Installation

### Prerequisites

- Python 3.8 or higher
- API keys for chosen LLM provider (OpenAI or Google Gemini)
- API keys for job platforms you intend to use (optional)

### Installation Steps

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/job-description-generator.git
   cd job-description-generator
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your configuration file:
   ```bash
   cp .env.template .env
   ```

5. Edit the `.env` file with your API keys and preferences.

6. Run the application:
   ```bash
   streamlit run app.py
   ```

## Configuration Guide

The application requires configuration through the `.env` file. Here are the key settings:

### LLM Provider Configuration

```
# LLM Provider selection (choose one)
LLM_PROVIDER=gemini  # or "openai"

# API Keys (fill in the one you're using)
GEMINI_API_KEY=your_gemini_api_key_here
OPENAI_API_KEY=your_openai_api_key_here

# Model settings
LLM_MODEL=gemini-pro  # For Gemini; use "gpt-4" for OpenAI
LLM_TEMPERATURE=0.7   # Controls creativity (0.0-1.0)
```

### Job Platform Configuration

```
# Preview Mode (set to False to enable actual posting)
PREVIEW_MODE=True

# Twitter Configuration
TWITTER_API_KEY=your_twitter_api_key
TWITTER_API_SECRET=your_twitter_api_secret
TWITTER_ACCESS_TOKEN=your_twitter_access_token
TWITTER_ACCESS_SECRET=your_twitter_access_secret
TWITTER_ENABLED=False

# Google Jobs Configuration
GOOGLE_JOBS_SERVICE_ACCOUNT_PATH=path/to/your/service-account-key.json
GOOGLE_CLOUD_PROJECT_ID=your-google-cloud-project-id
GOOGLE_JOBS_TENANT_ID=your-tenant-id
GOOGLE_JOBS_COMPANY_ID=your-company-id
GOOGLE_JOBS_ENABLED=False
```

### How to Get API Keys

#### Gemini API Key
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create an account or sign in
3. Click "Create API Key"
4. Copy the key to your `.env` file

#### OpenAI API Key
1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Create an account or sign in
3. Create a new API key
4. Copy the key to your `.env` file

#### Twitter API Keys
1. Apply for a [Twitter Developer Account](https://developer.twitter.com/en/portal/dashboard)
2. Create a Project and App with "Read and Write" permissions
3. Generate API keys and access tokens
4. Copy all four values to your `.env` file

#### Google Jobs API
1. Create a [Google Cloud Platform](https://console.cloud.google.com/) account
2. Create a new project
3. Enable the Cloud Talent Solution API
4. Create a service account and download the JSON key
5. Reference the path to this JSON file in your `.env` file

## Usage Instructions

### Web Interface

1. Start the application:
   ```bash
   streamlit run app.py
   ```

2. Navigate through the 4-step form:
   - **Step 1**: Enter company information and cultural values
   - **Step 2**: Specify technical requirements and tools
   - **Step 3**: Define role details and responsibilities
   - **Step 4**: Add specialized focus and other details

3. Click "Generate & Preview" (or "Generate & Post" if not in preview mode)

4. Review the generated job description and platform posting previews

5. Download the job description as Markdown or HTML if desired

### Command Line Interface

For batch processing or testing, use the CLI:

```bash
# Using an input JSON file
python simplified_cli.py --input example_input.json

# Save output to a file
python simplified_cli.py --input example_input.json --output my_job_description.md
```

## Customization Guide

### Modifying Form Fields and Options

To change the available options in dropdown menus (e.g., adding new roles or tools):

1. Edit `templates/form_template.py`:
   ```python
   STEP4_FIELDS = [
     {
        "key": "specialized_role_focus",
        "label": "Specialized Role Focus:",
        "type": "select",
        "options": ["Machine Learning Engineer", "UX Researcher", ...],  # Modify this list
        "required": True
     },
     # ...
   ]
   ```

2. Update the validation logic in `utils/validators.py` to match your new options:
   ```python
   valid_roles = [
       "Machine Learning Engineer", "UX Researcher", ...  # Should match options above
   ]
   ```

### Customizing Job Description Template

To change the structure of generated job descriptions:

1. Edit `templates/jd_template.py`:
   ```python
   JD_TEMPLATE = Template('''
   # **$role_title**
   **Location:** $location
   
   # Custom sections here...
   ''')
   ```

2. Update the `generate_jd` method in `agents/jd_generator.py` to include content for any new sections.

### Adding Custom Styling

To change the appearance of the job description in the web interface:

1. Modify the HTML styling in the `render_job_description` function in `app.py`
2. Update the HTML template in the export functionality

## API Integration

### Adding a New Job Platform

To add a new job posting platform:

1. Update `config/settings.py` to include the new platform configuration:
   ```python
   JOB_PLATFORMS = {
       # Existing platforms...
       "new_platform": {
           "enabled": os.getenv("NEW_PLATFORM_ENABLED", "False").lower() == "true",
           "api_url": "https://api.new-platform.com/endpoint",
       }
   }
   ```

2. Add the API key configuration to `.env.template` and your `.env` file:
   ```
   NEW_PLATFORM_API_KEY=your_api_key_here
   NEW_PLATFORM_ENABLED=False
   ```

3. Update `agents/job_poster.py` to include:
   - Platform-specific API initialization in `setup_platforms`
   - Content formatting in `format_for_platform`
   - Posting logic in `post_job`

### Changing AI Providers

The system supports both Google Gemini and OpenAI. To switch providers:

1. In the web interface, use the "Select AI Provider" dropdown in the sidebar
2. Through configuration, set `LLM_PROVIDER=gemini` or `LLM_PROVIDER=openai` in your `.env` file

To add a new AI provider:

1. Update `config/settings.py` to include the new provider
2. Add initialization and completion logic in `agents/jd_generator.py`
3. Update the UI in `app.py` to include the new provider option

## Troubleshooting

### Common Issues

1. **"API key not configured" error**
   - Check that you've added the correct API key to your `.env` file
   - Verify that the API key is valid
   - Ensure the `.env` file is in the correct location (project root)

2. **Validation errors**
   - Check that all required fields are filled in
   - Ensure dropdown selections match the valid options in `validators.py`
   - For role-specific errors, make sure `validators.py` is synchronized with form options

3. **Empty or poor quality job descriptions**
   - Check your API key has sufficient quota
   - Try adjusting the temperature setting
   - Ensure you're providing detailed information in the form inputs

4. **Platform posting issues**
   - Verify platform API keys are correct
   - Check that the platform is enabled in settings
   - Look for platform-specific error messages in the logs

### Logging

The application uses Python's logging module. To increase logging verbosity:

1. Set `LOG_LEVEL=DEBUG` in your `.env` file
2. Check terminal output for detailed logs

## Future Enhancements

Potential improvements for future versions:

1. **Additional AI Providers**: Support for more AI models like Anthropic Claude
2. **More Job Platforms**: Integration with LinkedIn, Indeed, and other major job sites
3. **Job Performance Tracking**: Analytics on job posting performance
4. **Template Library**: Predefined templates for different industries and roles
5. **Multilingual Support**: Generate job descriptions in multiple languages
6. **Collaborative Editing**: Allow multiple users to collaborate on job descriptions
7. **ATS Integration**: Direct integration with Applicant Tracking Systems
8. **Custom Branding**: Company logo and branding in generated job descriptions

---

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Streamlit](https://streamlit.io/) for the web interface
- [OpenAI](https://openai.com/) and [Google Gemini](https://makersuite.google.com/) for AI capabilities
- All contributors and testers who have helped improve this tool