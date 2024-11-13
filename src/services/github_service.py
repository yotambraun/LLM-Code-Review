from github import Github
from github.GithubException import GithubException
import aiohttp
import asyncio
from typing import List, Dict
import logging

class GitHubService:
    def __init__(self, token: str, repo: str):
        self.token = token
        self.repo = repo
        self.logger = logging.getLogger('github_service')
        # Initialize with proper auth header
        self.headers = {
            'Authorization': f'Bearer {self.token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        try:
            self.client = Github(self.token)
            # Verify credentials immediately
            self.client.get_user().login
            self.logger.info("Successfully authenticated with GitHub")
        except Exception as e:
            self.logger.error(f"Failed to initialize GitHub client: {str(e)}")
            raise

    async def get_pr_files(self, pr_number: int) -> List[Dict[str, str]]:
        """Fetch files from a pull request with improved error handling"""
        try:
            self.logger.info(f"Accessing repository: {self.repo}")
            self.logger.info(f"Fetching PR #{pr_number}")
            
            # Debug token (mask most of it)
            masked_token = f"{self.token[:4]}...{self.token[-4:]}"
            self.logger.info(f"Using token: {masked_token}")
            
            repo = self.client.get_repo(self.repo)
            self.logger.info(f"Successfully accessed repository")
            
            pr = repo.get_pull(pr_number)
            self.logger.info(f"Successfully accessed PR #{pr_number}")
            
            files = []
            async with aiohttp.ClientSession(headers=self.headers) as session:
                for file in pr.get_files():
                    if file.status != 'removed':
                        try:
                            content = await self._fetch_file_content(session, file.raw_url)
                            files.append({
                                'filename': file.filename,
                                'content': content,
                                'status': file.status
                            })
                        except Exception as e:
                            self.logger.error(f"Error fetching file {file.filename}: {str(e)}")
                            continue
            
            self.logger.info(f"Successfully fetched {len(files)} files")
            return files
            
        except GithubException as e:
            self.logger.error(f"GitHub API error: {e.status} - {e.data}")
            raise
        except Exception as e:
            self.logger.error(f"Error fetching PR files: {str(e)}")
            self.logger.error(f"Repository: {self.repo}")
            self.logger.error(f"PR Number: {pr_number}")
            raise

    async def _fetch_file_content(self, session: aiohttp.ClientSession, url: str) -> str:
        """Fetch content of a single file with retry logic"""
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(url) as response:
                    if response.status == 401:
                        self.logger.error("Authentication failed when fetching file")
                        raise Exception("Authentication failed")
                    response.raise_for_status()
                    return await response.text()
            except Exception as e:
                if attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff

    async def post_review(self, pr_number: int, review_body: str) -> Dict[str, str]:
        """Post a review comment on a pull request"""
        try:
            repo = self.client.get_repo(self.repo)
            pr = repo.get_pull(pr_number)
            comment = pr.create_issue_comment(review_body)
            self.logger.info(f"Successfully posted review comment")
            return {
                'status': 'success',
                'comment_id': str(comment.id),
                'url': comment.html_url
            }
        except Exception as e:
            self.logger.error(f"Error posting review: {str(e)}")
            raise

    def _validate_token(self) -> bool:
        """Validate the GitHub token"""
        try:
            self.client.get_user().login
            return True
        except Exception as e:
            self.logger.error(f"Token validation failed: {str(e)}")
            return False