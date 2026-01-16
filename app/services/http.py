"""HTTP client utilities."""
import requests
from typing import Optional
import time


class HTTPClient:
    """HTTP client with retry logic and error handling."""
    
    def __init__(self, timeout: int = 30, max_retries: int = 3, api_key: Optional[str] = None):
        self.timeout = timeout
        self.max_retries = max_retries
        self.api_key = api_key
        self.session = requests.Session()
        
    def get(self, url: str, headers: Optional[dict] = None, **kwargs) -> requests.Response:
        """Make GET request with retry logic."""
        if headers is None:
            headers = {}
        
        # Add default user agent if not provided
        if 'User-Agent' not in headers:
            headers['User-Agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        
        # Add API key if provided
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        
        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = self.session.get(
                    url,
                    headers=headers,
                    timeout=self.timeout,
                    **kwargs
                )
                response.raise_for_status()
                return response
            except requests.exceptions.RequestException as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    wait_time = 2 ** attempt
                    time.sleep(wait_time)
                    continue
                    
        raise last_exception
    
    def close(self):
        """Close the session."""
        self.session.close()
