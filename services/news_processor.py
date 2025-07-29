"""
News Processor Service
Handles processing, filtering, and categorizing news articles
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import re

from .llm_service import LLMService
from config import LLMConfig

logger = logging.getLogger(__name__)


class NewsProcessor:
    """News processing and categorization service"""
    
    def __init__(self, llm_config: LLMConfig):
        self.llm_service = LLMService(llm_config)
        self.keywords = {
            'technology': ['ai', 'artificial intelligence', 'machine learning', 'tech', 'software', 'hardware', 'startup', 'innovation'],
            'business': ['business', 'finance', 'economy', 'market', 'investment', 'company', 'corporate', 'startup'],
            'science': ['science', 'research', 'study', 'discovery', 'scientific', 'experiment', 'laboratory'],
            'politics': ['politics', 'government', 'election', 'policy', 'political', 'congress', 'senate', 'president'],
            'entertainment': ['movie', 'film', 'music', 'celebrity', 'entertainment', 'hollywood', 'streaming'],
            'sports': ['sports', 'football', 'basketball', 'baseball', 'soccer', 'athlete', 'game', 'championship'],
            'health': ['health', 'medical', 'medicine', 'disease', 'treatment', 'hospital', 'doctor', 'patient'],
            'environment': ['environment', 'climate', 'weather', 'pollution', 'sustainability', 'green', 'renewable']
        }
    
    async def process_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a list of articles with categorization and filtering"""
        if not articles:
            return []
        
        processed_articles = []
        
        for article in articles:
            try:
                processed_article = await self._process_single_article(article)
                if processed_article:
                    processed_articles.append(processed_article)
            except Exception as e:
                logger.error(f"Error processing article {article.get('id', 'unknown')}: {e}")
                continue
        
        logger.info(f"Processed {len(processed_articles)} articles from {len(articles)} total")
        return processed_articles
    
    async def _process_single_article(self, article: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single article"""
        # Add processing metadata
        processed_article = article.copy()
        processed_article['processed_at'] = datetime.now().isoformat()
        
        # Basic filtering
        if not self._is_valid_article(processed_article):
            return None
        
        # Categorize article
        category = await self._categorize_article(processed_article)
        processed_article['ai_category'] = category
        
        # Extract key points
        key_points = await self._extract_key_points(processed_article)
        if key_points:
            processed_article['key_points'] = key_points
        
        # Add relevance score
        processed_article['relevance_score'] = self._calculate_relevance_score(processed_article)
        
        return processed_article
    
    def _is_valid_article(self, article: Dict[str, Any]) -> bool:
        """Check if an article is valid for processing"""
        title = article.get('title', '').strip()
        description = article.get('description', '').strip()
        
        # Must have at least a title
        if not title:
            return False
        
        # Filter out very short titles (likely spam)
        if len(title) < 10:
            return False
        
        # Filter out articles with suspicious patterns
        suspicious_patterns = [
            r'\b(click here|read more|subscribe now)\b',
            r'\$\d+',
            r'\b(free|discount|sale|offer)\b',
            r'[A-Z]{5,}',  # Too many consecutive uppercase letters
        ]
        
        content = f"{title} {description}".lower()
        for pattern in suspicious_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                return False
        
        return True
    
    async def _categorize_article(self, article: Dict[str, Any]) -> str:
        """Categorize an article using AI and keyword matching"""
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # First try keyword-based categorization
        keyword_category = self._keyword_categorization(content)
        
        # If keyword categorization is confident, use it
        if keyword_category and self._is_keyword_confident(content, keyword_category):
            return keyword_category
        
        # Otherwise, use AI categorization
        try:
            ai_category = await self.llm_service.categorize_article(article)
            if ai_category:
                return ai_category
        except Exception as e:
            logger.warning(f"AI categorization failed: {e}")
        
        # Fallback to keyword categorization or default
        return keyword_category or 'other'
    
    def _keyword_categorization(self, content: str) -> Optional[str]:
        """Categorize article using keyword matching"""
        category_scores = {}
        
        for category, keywords in self.keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in content:
                    score += 1
            
            if score > 0:
                category_scores[category] = score
        
        if category_scores:
            # Return category with highest score
            return max(category_scores, key=category_scores.get)
        
        return None
    
    def _is_keyword_confident(self, content: str, category: str) -> bool:
        """Check if keyword categorization is confident enough"""
        if category not in self.keywords:
            return False
        
        keywords = self.keywords[category]
        matches = sum(1 for keyword in keywords if keyword.lower() in content)
        
        # Consider confident if at least 2 keywords match
        return matches >= 2
    
    async def _extract_key_points(self, article: Dict[str, Any]) -> Optional[List[str]]:
        """Extract key points from an article"""
        try:
            return await self.llm_service.extract_key_points(article)
        except Exception as e:
            logger.warning(f"Key points extraction failed: {e}")
            return None
    
    def _calculate_relevance_score(self, article: Dict[str, Any]) -> float:
        """Calculate a relevance score for the article"""
        score = 0.0
        
        title = article.get('title', '').lower()
        description = article.get('description', '').lower()
        content = f"{title} {description}"
        
        # Boost score for recent articles
        published_date = article.get('published_date')
        if published_date:
            try:
                pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                days_old = (datetime.now(pub_date.tzinfo) - pub_date).days
                if days_old <= 1:
                    score += 0.3
                elif days_old <= 3:
                    score += 0.2
                elif days_old <= 7:
                    score += 0.1
            except:
                pass
        
        # Boost score for articles with more content
        content_length = len(title) + len(description)
        if content_length > 200:
            score += 0.2
        elif content_length > 100:
            score += 0.1
        
        # Boost score for articles from reputable sources
        source = article.get('source', '').lower()
        reputable_sources = ['techcrunch', 'ars technica', 'the verge', 'bbc', 'reuters', 'wired']
        if any(reputable in source for reputable in reputable_sources):
            score += 0.2
        
        # Normalize score to 0-1 range
        return min(score, 1.0)
    
    def filter_articles_by_category(self, articles: List[Dict[str, Any]], category: str) -> List[Dict[str, Any]]:
        """Filter articles by category"""
        return [article for article in articles if article.get('ai_category') == category]
    
    def filter_articles_by_relevance(self, articles: List[Dict[str, Any]], min_score: float = 0.3) -> List[Dict[str, Any]]:
        """Filter articles by relevance score"""
        return [article for article in articles if article.get('relevance_score', 0) >= min_score]
    
    def sort_articles_by_relevance(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Sort articles by relevance score (highest first)"""
        return sorted(articles, key=lambda x: x.get('relevance_score', 0), reverse=True) 