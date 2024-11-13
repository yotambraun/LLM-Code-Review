from typing import List, Dict
import aiohttp
from github import Github
from src.utils.logger import setup_logger

class GitHubService:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.client = Github(token)
        self.logger = setup_logger('github_service')
    
    async def get_pr_files(self, pr_number: int) -> List[Dict[str, str]]:
        """Fetch files from a pull request"""
        try:
            repo = self.client.get_repo(self.repo)
            pr = repo.get_pull(pr_number)
            files = []
            
            async with aiohttp.ClientSession() as session:
                for file in pr.get_files():
                    if file.status != 'removed':
                        content = await self._fetch_file_content(
                            session, file.raw_url
                        )
                        files.append({
                            'filename': file.filename,
                            'content': content,
                            'status': file.status,
                            'additions': file.additions,
                            'deletions': file.deletions
                        })
            return files
            
        except Exception as e:
            self.logger.error(f"Error fetching PR files: {str(e)}")
            raise
    
    async def _fetch_file_content(
        self, session: aiohttp.ClientSession, url: str
    ) -> str:
        """Fetch content of a single file"""
        async with session.get(
            url, headers={'Authorization': f'token {self.token}'}
        ) as response:
            return await response.text()
    
    async def post_review(
        self, pr_number: int, review_body: str
    ) -> Dict[str, str]:
        """Post a review comment on a pull request"""
        try:
            repo = self.client.get_repo(self.repo)
            pr = repo.get_pull(pr_number)
            comment = pr.create_issue_comment(review_body)
            return {
                'status': 'success',
                'comment_id': str(comment.id),
                'url': comment.html_url
            }
        except Exception as e:
            self.logger.error(f"Error posting review: {str(e)}")
            raise