import asyncio
import os
import sys
from src.services.github_service import GitHubService
from src.services.openai_service import OPENAIService
from src.config.settings import APISettings, ReviewSettings
from src.review.review_manager import ReviewManager

async def main(pr_number: int):
    try:
        api_settings = APISettings.from_env()
        review_settings = ReviewSettings()
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
        result = await review_manager.process_pull_request(pr_number)
        
        if result['status'] == 'success':
            print(f"Review completed successfully for PR #{pr_number}")
            return 0
        else:
            print(f"Review failed: {result.get('message', 'Unknown error')}")
            return 1
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python main.py <pr_number>")
        sys.exit(1)
        
    pr_number = int(sys.argv[1])
    
    if os.name == 'nt':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    exit_code = asyncio.run(main(pr_number))
    sys.exit(exit_code)