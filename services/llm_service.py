"""
LLM Service for AI News Bot
Handles AI-powered summarization and analysis of news articles
"""

import logging
from typing import Dict, Any, Optional, List
from langchain_ollama import OllamaLLM
from datetime import datetime

from config import LLMConfig

logger = logging.getLogger(__name__)


class LLMService:
    """LLM service for AI-powered text processing"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.llm = OllamaLLM(model=config.model)
    
    async def summarize_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Generate an AI summary of an article"""
        try:
            # Prepare the content for summarization
            title = article.get('title', '')
            description = article.get('description', '')
            
            if not title and not description:
                logger.warning(f"No content to summarize for article {article.get('id', 'unknown')}")
                return None
            
            # Create the prompt for summarization
            prompt = self._create_summary_prompt(title, description)
            
            # Call OpenAI API
            response = await self._call_openai(prompt)
            
            if not response:
                return None
            
            # Parse and structure the response
            summary_data = {
                'article_id': article.get('id'),
                'summary': response,
                'generated_at': datetime.now().isoformat(),
                'model': self.config.model,
                'word_count': len(response.split()),
                'original_title': title,
                'original_description': description[:200] + "..." if len(description) > 200 else description
            }
            
            logger.info(f"Generated summary for article {article.get('id', 'unknown')}")
            return summary_data
            
        except Exception as e:
            logger.error(f"Error summarizing article {article.get('id', 'unknown')}: {e}")
            return None
    
    async def categorize_article(self, article: Dict[str, Any]) -> Optional[str]:
        """Categorize an article using AI"""
        try:
            title = article.get('title', '')
            description = article.get('description', '')
            
            if not title:
                return None
            
            prompt = self._create_categorization_prompt(title, description)
            response = await self._call_openai(prompt)
            
            if response:
                # Clean up the response
                category = response.strip().lower()
                return category
            
            return None
            
        except Exception as e:
            logger.error(f"Error categorizing article: {e}")
            return None
    
    async def extract_key_points(self, article: Dict[str, Any]) -> Optional[List[str]]:
        """Extract key points from an article"""
        try:
            title = article.get('title', '')
            description = article.get('description', '')
            
            if not title and not description:
                return None
            
            prompt = self._create_key_points_prompt(title, description)
            response = await self._call_openai(prompt)
            
            if response:
                # Parse the response into a list of key points
                key_points = [point.strip() for point in response.split('\n') if point.strip()]
                return key_points
            
            return None
            
        except Exception as e:
            logger.error(f"Error extracting key points: {e}")
            return None
    
    def _create_summary_prompt(self, title: str, description: str) -> str:
        """Create a prompt for article summarization"""
        content = f"Title: {title}\n\nDescription: {description}"
        
        return f"""Please provide a concise summary of the following news article. 
Focus on the main points and key information. Keep the summary under {self.config.summary_max_length} characters.

Article:
{content}

Summary:"""
    
    def _create_categorization_prompt(self, title: str, description: str) -> str:
        """Create a prompt for article categorization"""
        content = f"Title: {title}\n\nDescription: {description}"
        
        return f"""Please categorize the following news article into one of these categories:
- technology
- business
- science
- politics
- entertainment
- sports
- health
- environment
- other

Article:
{content}

Category:"""
    
    def _create_key_points_prompt(self, title: str, description: str) -> str:
        """Create a prompt for extracting key points"""
        content = f"Title: {title}\n\nDescription: {description}"
        
        return f"""Please extract 3-5 key points from the following news article. 
Present each point on a new line, starting with a bullet point.

Article:
{content}

Key Points:"""
    
    async def _call_openai(self, prompt: str) -> Optional[str]:
        """Make a call to OpenAI API"""
        try:
            response = await self.llm.invoke(prompt)
            
            if response.choices and response.choices[0].message:
                return response.choices[0].message.content.strip()
            
            return None
            
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None
    
    async def batch_summarize(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Summarize multiple articles in batch"""
        summaries = []
        
        for article in articles:
            summary = await self.summarize_article(article)
            if summary:
                summaries.append(summary)
        
        logger.info(f"Generated {len(summaries)} summaries from {len(articles)} articles")
        return summaries 