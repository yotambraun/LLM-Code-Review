from typing import Dict
import asyncio
from openai import OpenAI
import backoff
from src.utils.logger import setup_logger

class OPENAIService:
    def __init__(self, api_key: str, model: str, timeout: int, max_retries: int):
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self.logger = setup_logger('ai_service')
    
    @backoff.on_exception(
        backoff.expo,
        (Exception),
        max_tries=2,
        max_time=30
    )
    async def generate_review(self, file_data: Dict) -> Dict[str, str]:
        """Generate code review using openAI"""
        try:
            prompt = self._create_review_prompt(file_data)
            response = await asyncio.to_thread(
                self._make_ai_request, prompt
            )
            return self._parse_ai_response(response)
        except Exception as e:
            self.logger.error(f"AI review generation failed: {str(e)}")
            raise
    
    def _create_review_prompt(self, file_data: Dict) -> str:
        """Create a detailed prompt for the openAI review"""
        return f"""
        As an expert code reviewer, analyze this {file_data['filename']} file:
        
        Focus areas:
        1. Code quality and best practices
        2. Potential bugs and issues
        3. Performance considerations
        4. Security implications
        
        File content:
        {file_data['content']}
        
        Provide specific, actionable feedback with examples where applicable.
        """
    
    def _make_ai_request(self, prompt: str) -> Dict:
        """Make the actual API request to OpenAI"""
        return self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert code reviewer"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2,
            timeout=self.timeout
        )
    
    def _parse_ai_response(self, response: Dict) -> Dict[str, str]:
        """Parse and structure the openAI response"""
        return {
            'review': response.choices[0].message.content,
            'model': self.model,
            'tokens_used': response.usage.total_tokens
        }