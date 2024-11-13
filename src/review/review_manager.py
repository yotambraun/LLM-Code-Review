from typing import List, Dict
import asyncio
from datetime import datetime
from src.services.github_service import GitHubService
from src.services.openai_service import OPENAIService
from src.utils.logger import setup_logger
from src.config.settings import ReviewSettings

class ReviewManager:
    def __init__(
        self,
        github_service: GitHubService,
        ai_service: OPENAIService,
        settings: ReviewSettings
    ):
        self.github = github_service
        self.ai = ai_service
        self.settings = settings
        self.logger = setup_logger('review_manager')
    
    async def process_pull_request(self, pr_number: int) -> Dict:
        """Process a complete pull request review"""
        try:
            files = await self.github.get_pr_files(pr_number)
            review_files = [
                f for f in files
                if self.settings.is_file_allowed(f['filename'])
                and len(f['content'].encode()) < self.settings.max_file_size_kb * 1024
            ]
            
            if not review_files:
                return {'status': 'no_files', 'message': 'No files to review'}
            
            reviews = []
            for batch in self._batch_files(review_files):
                batch_reviews = await asyncio.gather(*[
                    self.ai.generate_review(file)
                    for file in batch
                ])
                reviews.extend(batch_reviews)
            summary = self._create_review_summary(reviews)
            await self.github.post_review(pr_number, summary)
            
            return {
                'status': 'success',
                'reviews': reviews,
                'summary': summary,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Review process failed: {str(e)}")
            return {'status': 'error', 'message': str(e)}
    
    def _batch_files(self, files: List[Dict]) -> List[List[Dict]]:
        """Split files into batches for processing"""
        return [
            files[i:i + self.settings.review_batch_size]
            for i in range(0, len(files), self.settings.review_batch_size)
        ]
    
    def _create_review_summary(self, reviews: List[Dict]) -> str:
        """Create a formatted summary of all reviews"""
        summary = "# Pull Request Review Summary\n\n"
        
        for idx, review in enumerate(reviews, 1):
            summary += f"## File {idx}: {review.get('filename', 'Unknown')}\n"
            summary += f"{review.get('review', 'No review generated')}\n\n"
        
        summary += "\n## Overall Recommendations\n"
        summary += self._generate_overall_recommendations(reviews)
        
        return summary
    
    def _generate_overall_recommendations(self, reviews: List[Dict]) -> str:
        """Generate overall recommendations from all reviews"""
        return "\n".join([
            "### Key Points:",
            "- Keep code consistent with project standards",
            "- Address any security concerns highlighted above",
            "- Consider performance implications of changes",
            "- Ensure proper error handling is in place",
            "\nPlease review and address the feedback above."
        ])