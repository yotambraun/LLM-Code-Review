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
        self.headers = {
            'Authorization': f'token {self.token}',  
            'Accept': 'application/vnd.github.v3+json',
            'X-GitHub-Api-Version': '2022-11-28' 
        }
        try:
            self.client = Github(self.token)
            self.repo_obj = self.client.get_repo(self.repo)
            self.logger.info(f"Successfully initialized GitHub client for repository: {self.repo}")
        except Exception as e:
            self.logger.error(f"Failed to initialize GitHub client: {str(e)}")
            raise

    async def get_pr_files(self, pr_number: int) -> List[Dict[str, str]]:
        """Fetch files from a pull request with improved error handling"""
        try:
            self.logger.info(f"Accessing repository: {self.repo}")
            self.logger.info(f"Fetching PR #{pr_number}")
            
            masked_token = f"{self.token[:4]}...{self.token[-4:]}" if len(self.token) > 8 else "***"
            self.logger.info(f"Using token: {masked_token}")
            
            try:
                pr = self.repo_obj.get_pull(pr_number)
                self.logger.info(f"Successfully accessed PR #{pr_number}")
            except GithubException as e:
                self.logger.error(f"Failed to access PR {pr_number}: {e.data.get('message', str(e))}")
                raise
            
            files = []
            async with aiohttp.ClientSession() as session:
                for file in pr.get_files():
                    if file.status != 'removed':
                        try:
                            headers = {
                                'Authorization': f'token {self.token}',
                                'Accept': 'application/vnd.github.v3.raw'
                            }
                            content = await self._fetch_file_content(session, file.raw_url, headers)
                            files.append({
                                'filename': file.filename,
                                'content': content,
                                'status': file.status,
                                'additions': file.additions,
                                'deletions': file.deletions
                            })
                            self.logger.info(f"Successfully fetched file: {file.filename}")
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

    async def _fetch_file_content(
        self, 
        session: aiohttp.ClientSession, 
        url: str,
        headers: Dict[str, str]
    ) -> str:
        """Fetch content of a single file with retry logic"""
        MAX_RETRIES = 3
        for attempt in range(MAX_RETRIES):
            try:
                async with session.get(url, headers=headers) as response:
                    if response.status == 401 or response.status == 403:
                        error_msg = await response.text()
                        self.logger.error(f"Authentication failed when fetching file: {error_msg}")
                        raise Exception(f"Authentication failed: {error_msg}")
                    response.raise_for_status()
                    return await response.text()
            except aiohttp.ClientError as e:
                self.logger.error(f"Request failed (attempt {attempt + 1}/{MAX_RETRIES}): {str(e)}")
                if attempt == MAX_RETRIES - 1:
                    raise
                await asyncio.sleep(2 ** attempt)

    async def post_review(self, pr_number: int, review_body: str) -> Dict[str, str]:
        """Post a review comment on a pull request"""
        try:
            if not hasattr(self, 'repo_obj'):
                self.repo_obj = self.client.get_repo(self.repo)
                
            pr = self.repo_obj.get_pull(pr_number)
            comment = pr.create_issue_comment(review_body)
            self.logger.info(f"Successfully posted review comment on PR #{pr_number}")
            return {
                'status': 'success',
                'comment_id': str(comment.id),
                'url': comment.html_url
            }
        except GithubException as e:
            self.logger.error(f"GitHub API error while posting review: {e.status} - {e.data}")
            raise
        except Exception as e:
            self.logger.error(f"Error posting review: {str(e)}")
            raise

    def validate_access(self) -> bool:
        """Validate repository access"""
        try:
            if not hasattr(self, 'repo_obj'):
                self.repo_obj = self.client.get_repo(self.repo)
            
            _ = self.repo_obj.full_name
            self.logger.info(f"Successfully validated access to repository: {self.repo}")
            return True
        except Exception as e:
            self.logger.error(f"Repository access validation failed: {str(e)}")
            return False