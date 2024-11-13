from dataclasses import dataclass
from typing import List
import os
from dotenv import load_dotenv

@dataclass
class ReviewSettings:
    """Review configuration settings"""
    categories: List[str] = ('security', 'performance', 'style', 'conventions')
    max_file_size_kb: int = 500
    excluded_patterns: List[str] = ('*.pyc', '*.env', '__pycache__/*', '*.log')
    review_batch_size: int = 5
    
    def is_file_allowed(self, filename: str) -> bool:
        """Check if file should be reviewed based on patterns"""
        import fnmatch
        return not any(fnmatch.fnmatch(filename, pattern) 
                      for pattern in self.excluded_patterns)

@dataclass
class APISettings:
    """API configuration settings"""
    git_token: str
    openai_api_key: str
    github_repo: str
    model_name: str = "gpt-4"
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: int = 2

    @classmethod
    def from_env(cls) -> 'APISettings':
        """Create settings from environment variables"""
        load_dotenv()
        required_vars = {
            'git_token': os.getenv('GIT_TOKEN'),
            'openai_api_key': os.getenv('OPENAI_API_KEY'),
            'github_repo': os.getenv('GITHUB_REPOSITORY')
        }
        
        missing = [k for k, v in required_vars.items() if not v]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
            
        return cls(**required_vars)