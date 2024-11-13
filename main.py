import asyncio
import os
import sys
from typing import Optional
from github import Github
from src.services.github_service import GitHubService
from src.services.openai_service import OPENAIService
from src.config.settings import APISettings, ReviewSettings
from src.review.review_manager import ReviewManager
from src.utils.logger import setup_logger

logger = setup_logger('main')

async def validate_environment() -> Optional[str]:
    """
    Validate all required environment variables and credentials
    Returns error message if validation fails, None if successful
    """
    # Check required environment variables
    required_vars = {
        'GIT_TOKEN': os.getenv('GIT_TOKEN'),
        'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY'),
        'GITHUB_REPOSITORY': os.getenv('GITHUB_REPOSITORY')
    }
    
    missing_vars = [k for k, v in required_vars.items() if not v]
    if missing_vars:
        return f"Missing required environment variables: {', '.join(missing_vars)}"
    
    # Validate GitHub token by checking repository access instead of user access
    try:
        github = Github(required_vars['GIT_TOKEN'])
        repo = github.get_repo(required_vars['GITHUB_REPOSITORY'])
        # Just check if we can access basic repo info
        _ = repo.full_name
        logger.info(f"Successfully validated GitHub token for repository: {repo.full_name}")
    except Exception as e:
        return f"GitHub token validation failed: {str(e)}"
    
    return None

async def main(pr_number: int) -> int:
    """
    Main function to run the code review process
    Returns exit code (0 for success, 1 for failure)
    """
    try:
        logger.info("Starting code review process")
        logger.info(f"PR Number: {pr_number}")
        logger.info(f"Repository: {os.getenv('GITHUB_REPOSITORY')}")
        error = await validate_environment()
        if error:
            logger.error(error)
            return 1
        
        try:
            api_settings = APISettings.from_env()
            review_settings = ReviewSettings()
        except Exception as e:
            logger.error(f"Failed to initialize settings: {str(e)}")
            return 1
            
        try:
            github_service = GitHubService(
                api_settings.git_token,
                api_settings.github_repo
            )
            
            ai_service = OPENAIService(
                api_settings.openai_api_key,
                api_settings.model_name,
                api_settings.request_timeout,
                api_settings.max_retries
            )
            
            review_manager = ReviewManager(
                github_service,
                ai_service,
                review_settings
            )
        except Exception as e:
            logger.error(f"Failed to initialize services: {str(e)}")
            return 1
        
        try:
            result = await review_manager.process_pull_request(pr_number)
            
            if result['status'] == 'success':
                logger.info(f"Review completed successfully for PR #{pr_number}")
                return 0
            else:
                logger.error(f"Review failed: {result.get('message', 'Unknown error')}")
                return 1
                
        except Exception as e:
            logger.error(f"Error during review process: {str(e)}")
            return 1
            
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 1

def print_debug_info(pr_number: str) -> None:
    """Print debug information about environment"""
    debug_info = {
        "PR Number": pr_number,
        "Repository": os.getenv('GITHUB_REPOSITORY'),
        "Has GIT_TOKEN": 'Yes' if os.getenv('GIT_TOKEN') else 'No',
        "Has OPENAI_API_KEY": 'Yes' if os.getenv('OPENAI_API_KEY') else 'No',
        "Python Version": sys.version,
        "Platform": sys.platform
    }
    
    logger.info("Debug Information:")
    for key, value in debug_info.items():
        logger.info(f"{key}: {value}")

if __name__ == "__main__":
    try:
        if len(sys.argv) != 2:
            logger.error("Usage: python main.py <pr_number>")
            sys.exit(1)
            
        pr_number = int(sys.argv[1])
        print_debug_info(sys.argv[1])
        
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        exit_code = asyncio.run(main(pr_number))
        sys.exit(exit_code)
        
    except ValueError:
        logger.error("Invalid PR number provided")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start application: {str(e)}")
        sys.exit(1)