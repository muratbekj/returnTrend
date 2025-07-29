"""
RSS Scraper Service
Handles fetching and parsing RSS feeds
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import aiohttp
import feedparser
from urllib.parse import urlparse

from config import RSSFeed

logger = logging.getLogger(__name__)


class RSSScraper:
    """RSS feed scraper service"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={
                'User-Agent': 'AI-News-Bot/1.0 (RSS Scraper)'
            }
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def fetch_feed(self, feed: RSSFeed) -> List[Dict[str, Any]]:
        """Fetch and parse a single RSS feed"""
        if not self.session:
            raise RuntimeError("Scraper not initialized. Use async context manager.")
        
        try:
            logger.info(f"Fetching feed: {feed.name} ({feed.url})")
            
            async with self.session.get(feed.url) as response:
                if response.status != 200:
                    logger.error(f"Failed to fetch {feed.name}: HTTP {response.status}")
                    return []
                
                content = await response.text()
                
                # Parse RSS feed
                parsed_feed = feedparser.parse(content)
                
                if parsed_feed.bozo:
                    logger.warning(f"Feed {feed.name} has parsing issues: {parsed_feed.bozo_exception}")
                
                articles = []
                for entry in parsed_feed.entries:
                    article = self._parse_entry(entry, feed)
                    if article:
                        articles.append(article)
                
                logger.info(f"Fetched {len(articles)} articles from {feed.name}")
                return articles
                
        except Exception as e:
            logger.error(f"Error fetching feed {feed.name}: {e}")
            return []
    
    def _parse_entry(self, entry, feed: RSSFeed) -> Optional[Dict[str, Any]]:
        """Parse a single RSS entry into a standardized article format"""
        try:
            # Extract basic information
            title = getattr(entry, 'title', '').strip()
            link = getattr(entry, 'link', '').strip()
            
            if not title or not link:
                return None
            
            # Extract description/summary
            description = ''
            if hasattr(entry, 'summary'):
                description = entry.summary.strip()
            elif hasattr(entry, 'description'):
                description = entry.description.strip()
            
            # Extract publication date
            published_date = None
            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                published_date = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
            elif hasattr(entry, 'updated_parsed') and entry.updated_parsed:
                published_date = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)
            
            # Extract author
            author = ''
            if hasattr(entry, 'author'):
                author = entry.author.strip()
            
            # Generate unique ID
            article_id = self._generate_article_id(link, title)
            
            return {
                'id': article_id,
                'title': title,
                'link': link,
                'description': description,
                'author': author,
                'published_date': published_date.isoformat() if published_date else None,
                'source': feed.name,
                'category': feed.category,
                'feed_url': feed.url,
                'scraped_at': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error parsing entry: {e}")
            return None
    
    def _generate_article_id(self, link: str, title: str) -> str:
        """Generate a unique ID for an article"""
        import hashlib
        
        # Use link and title to generate a hash
        content = f"{link}:{title}".encode('utf-8')
        return hashlib.md5(content).hexdigest()
    
    async def fetch_all_feeds(self, feeds: List[RSSFeed]) -> List[Dict[str, Any]]:
        """Fetch all RSS feeds concurrently"""
        if not feeds:
            return []
        
        async with self:
            tasks = [self.fetch_feed(feed) for feed in feeds if feed.enabled]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            all_articles = []
            for result in results:
                if isinstance(result, list):
                    all_articles.extend(result)
                else:
                    logger.error(f"Feed fetch failed: {result}")
            
            # Remove duplicates based on article ID
            seen_ids = set()
            unique_articles = []
            for article in all_articles:
                if article['id'] not in seen_ids:
                    seen_ids.add(article['id'])
                    unique_articles.append(article)
            
            logger.info(f"Total unique articles fetched: {len(unique_articles)}")
            return unique_articles 