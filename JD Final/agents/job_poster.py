import requests
import json
import logging
import os
from typing import Dict, List
from config.settings import JOB_PLATFORMS, TWITTER_API_KEY, TWITTER_API_SECRET
from config.settings import TWITTER_ACCESS_TOKEN, TWITTER_ACCESS_SECRET
from config.settings import GOOGLE_JOBS_SERVICE_ACCOUNT_PATH

logger = logging.getLogger(__name__)

class JobPoster:
    """Agent for posting job descriptions to various platforms"""
    
    def __init__(self, preview_mode=True):
        """Initialize the job poster
        
        Args:
            preview_mode: If True, only simulate posting without actually sending to platforms
        """
        self.platforms = JOB_PLATFORMS
        self.preview_mode = preview_mode
        self.setup_platforms()
    
    def setup_platforms(self):
        """Set up API clients for each enabled platform"""
        
        # Setup Twitter API client
        if self.platforms["twitter"]["enabled"]:
            try:
                import tweepy
                self.twitter_client = tweepy.Client(
                    consumer_key=TWITTER_API_KEY,
                    consumer_secret=TWITTER_API_SECRET,
                    access_token=TWITTER_ACCESS_TOKEN,
                    access_token_secret=TWITTER_ACCESS_SECRET
                )
                logger.info("Twitter API client set up successfully")
            except Exception as e:
                logger.error(f"Failed to set up Twitter API client: {str(e)}")
                self.platforms["twitter"]["enabled"] = False
        
        # Setup Google Jobs API client
        if self.platforms["google_jobs"]["enabled"]:
            try:
                # Import Google Cloud libraries
                from google.cloud import talent
                from google.oauth2 import service_account
                
                # Setup credentials from service account file
                if GOOGLE_JOBS_SERVICE_ACCOUNT_PATH and os.path.exists(GOOGLE_JOBS_SERVICE_ACCOUNT_PATH):
                    credentials = service_account.Credentials.from_service_account_file(
                        GOOGLE_JOBS_SERVICE_ACCOUNT_PATH
                    )
                    self.google_jobs_client = talent.CompanyServiceClient(credentials=credentials)
                    self.google_jobs_job_client = talent.JobServiceClient(credentials=credentials)
                    logger.info("Google Jobs API client set up successfully")
                else:
                    raise FileNotFoundError("Google Jobs service account file not found")
            except Exception as e:
                logger.error(f"Failed to set up Google Jobs API client: {str(e)}")
                self.platforms["google_jobs"]["enabled"] = False
        
        # Setup for other platforms would go here
        # PLACEHOLDER: Add Naukri API setup
        # PLACEHOLDER: Add Upwork API setup
    
    def format_for_platform(self, job_description: str, platform: str) -> Dict:
        """Format job description appropriately for each platform"""
        if platform == "twitter":
            # Twitter has character limits, so create a summary
            lines = job_description.split("\n")
            role_title = ""
            location = ""
            
            for line in lines:
                if "**Position:**" in line:
                    role_title = line.replace("**Position:**", "").strip()
                elif "**Location:**" in line:
                    location = line.replace("**Location:**", "").strip()
            
            # Create a concise tweet with the role and a link (normally you'd add a link to the full job posting)
            summary = f"We're hiring! {role_title} - {location}. Apply now! #JobOpening #Hiring #Careers"
            
            # Twitter has 280 character limit
            if len(summary) > 280:
                summary = summary[:277] + "..."
                
            return {"text": summary}
        
        elif platform == "google_jobs":
            # Extract necessary information for Google Jobs API
            lines = job_description.split("\n")
            role_title = ""
            location = ""
            employment_type = ""
            description = job_description  # Use full description
            
            for line in lines:
                if "**Position:**" in line:
                    role_title = line.replace("**Position:**", "").strip()
                elif "**Location:**" in line:
                    location = line.replace("**Location:**", "").strip()
                elif "**Employment Type:**" in line:
                    employment_type = line.replace("**Employment Type:**", "").strip()
            
            # Map employment type to Google's format
            employment_types = []
            if "Full-Time" in employment_type:
                employment_types.append("FULL_TIME")
            elif "Part-Time" in employment_type:
                employment_types.append("PART_TIME")
            elif "Contract" in employment_type:
                employment_types.append("CONTRACTOR")
            elif "Freelance" in employment_type:
                employment_types.append("TEMPORARY")
            else:
                employment_types.append("FULL_TIME")  # Default
            
            # Extract location
            addresses = [location.strip()]
            
            return {
                "title": role_title,
                "description": description,
                "addresses": addresses,
                "employment_types": employment_types
            }
        
        elif platform == "naukri":
            # PLACEHOLDER: Format for Naukri job API
            # Would need actual API documentation to implement properly
            lines = job_description.split("\n")
            position = next((line for line in lines if "Position:" in line), "").replace("**Position:**", "").strip()
            location = next((line for line in lines if "Location:" in line), "").replace("**Location:**", "").strip()
            
            return {
                "title": position,
                "location": location,
                "description": job_description,
                "employmentType": "FULL_TIME"  # Extract from job description
            }
        
        elif platform == "upwork":
            # PLACEHOLDER: Format for Upwork API
            # Would need actual API documentation to implement properly
            lines = job_description.split("\n")
            position = next((line for line in lines if "Position:" in line), "").replace("**Position:**", "").strip()
            
            return {
                "title": position,
                "description": job_description,
                "category": "Web, Mobile & Software Dev",  # Would need mapping logic
                "subcategory": "Web Development",          # Would need mapping logic
                "budget": {
                    "amount": 1000,                        # Placeholder
                    "currencyCode": "USD"
                }
            }
        
        return {"content": job_description}
    
    def post_job(self, job_description: str) -> Dict[str, Dict]:
        """Post job to all enabled platforms and return results"""
        
        # If in preview mode, use mock posting
        if self.preview_mode:
            return self.mock_post_job(job_description)
        
        results = {}
        
        for platform, config in self.platforms.items():
            if not config["enabled"]:
                logger.info(f"Skipping {platform} - not enabled")
                results[platform] = {
                    "success": False,
                    "message": "Platform not enabled"
                }
                continue
            
            try:
                formatted_job = self.format_for_platform(job_description, platform)
                
                if platform == "twitter":
                    # Actual Twitter posting
                    response = self.twitter_client.create_tweet(text=formatted_job["text"])
                    tweet_id = response.data.get("id") if response.data else None
                    success = bool(tweet_id)
                    message = f"Posted to Twitter. Tweet ID: {tweet_id}" if success else "Failed to post to Twitter"
                
                elif platform == "google_jobs":
                    # Actual Google Jobs posting
                    from google.cloud import talent
                    
                    # First, you need a company in Google Jobs
                    # This would typically be done once, not for every job posting
                    project_id = "your-google-cloud-project-id"  # Replace with your project ID
                    tenant_id = "your-tenant-id"  # You'd create this once in Google Cloud
                    parent = f"projects/{project_id}/tenants/{tenant_id}"
                    
                    # Create a job
                    job = talent.Job(
                        company=f"{parent}/companies/your-company-id",  # You'd create this once
                        title=formatted_job["title"],
                        description=formatted_job["description"],
                        addresses=formatted_job["addresses"],
                        employment_types=formatted_job["employment_types"]
                    )
                    
                    # Create the job
                    response = self.google_jobs_job_client.create_job(parent=parent, job=job)
                    job_name = response.name if response else None
                    success = bool(job_name)
                    message = f"Posted to Google Jobs. Job ID: {job_name}" if success else "Failed to post to Google Jobs"
                
                elif platform == "naukri":
                    # PLACEHOLDER: Actual Naukri posting
                    # Would need actual API implementation
                    success = False
                    message = "Naukri integration not implemented. Add API integration code here."
                
                elif platform == "upwork":
                    # PLACEHOLDER: Actual Upwork posting
                    # Would need actual API implementation
                    success = False
                    message = "Upwork integration not implemented. Add API integration code here."
                
                results[platform] = {
                    "success": success,
                    "message": message
                }
                
            except Exception as e:
                logger.error(f"Error posting to {platform}: {str(e)}")
                results[platform] = {
                    "success": False,
                    "message": f"Error: {str(e)}"
                }
        
        return results

    def mock_post_job(self, job_description: str) -> Dict[str, Dict]:
        """Mock post job to all platforms (for testing or preview)"""
        results = {}
        
        for platform in self.platforms.keys():
            # Create formatted preview of what would be posted
            formatted_job = self.format_for_platform(job_description, platform)
            
            # Generate platform-specific preview message
            if platform == "twitter":
                preview = f"Would tweet: \"{formatted_job['text']}\""
            elif platform == "google_jobs":
                preview = f"Would post job: \"{formatted_job['title']}\" to Google Jobs"
            elif platform == "naukri":
                preview = f"Would post job: \"{formatted_job['title']}\" to Naukri"
            elif platform == "upwork":
                preview = f"Would post job: \"{formatted_job['title']}\" to Upwork"
            else:
                preview = f"Would post to {platform}"
            
            # Simulate successful posting
            results[platform] = {
                "success": True,
                "message": f"PREVIEW MODE: {preview}",
                "formatted_data": formatted_job  # Include the formatted data for reference
            }
        
        return results