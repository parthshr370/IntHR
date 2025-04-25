import requests
import json
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class APIConnector:
    """Utility class for connecting to external APIs"""
    
    @staticmethod
    def make_request(
        method: str,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        auth: Optional[tuple] = None,
        timeout: int = 30
    ) -> Dict[str, Any]:
        """Make a request to an external API"""
        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                data=json.dumps(data) if data else None,
                auth=auth,
                timeout=timeout
            )
            
            response.raise_for_status()
            
            return {
                "success": True,
                "status_code": response.status_code,
                "data": response.json() if response.content else {},
                "message": "Request successful"
            }
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP Error: {str(e)}")
            return {
                "success": False,
                "status_code": e.response.status_code if hasattr(e, "response") else None,
                "data": {},
                "message": f"HTTP Error: {str(e)}"
            }
        
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Connection Error: {str(e)}")
            return {
                "success": False,
                "status_code": None,
                "data": {},
                "message": f"Connection Error: {str(e)}"
            }
        
        except requests.exceptions.Timeout as e:
            logger.error(f"Timeout Error: {str(e)}")
            return {
                "success": False,
                "status_code": None,
                "data": {},
                "message": f"Timeout Error: {str(e)}"
            }
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Request Exception: {str(e)}")
            return {
                "success": False,
                "status_code": None,
                "data": {},
                "message": f"Request Exception: {str(e)}"
            }
        
        except Exception as e:
            logger.error(f"Unexpected Error: {str(e)}")
            return {
                "success": False,
                "status_code": None,
                "data": {},
                "message": f"Unexpected Error: {str(e)}"
            }