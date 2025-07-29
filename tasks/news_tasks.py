"""
News Scraping and Processing Tasks
Background tasks for fetching and processing news articles
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any

from config import config
from services.scraper import RSSScraper
from services.news_processor import NewsProcessor
from services.llm_service import LLMService
from utils.storage import save_articles, load_articles, save_summaries, load_summaries

logger = logging.getLogger(__name__)


class NewsTasks:
    """Background tasks for news scraping and processing"""
    
    def __init__(self):
        self.scraper = RSSScraper()
        self.processor = NewsProcessor(config.llm)
        self.llm_service = LLMService(config.llm)
    
    async def scrape_and_process_news(self):
        """Main task: scrape RSS feeds and process articles"""
        try:
            logger.info("Starting news scraping and processing task")
            
            # Step 1: Scrape RSS feeds
            articles = await self._scrape_news()
            if not articles:
                logger.warning("No articles scraped from RSS feeds")
                return
            
            # Step 2: Process articles (categorize, filter, etc.)
            processed_articles = await self._process_articles(articles)
            if not processed_articles:
                logger.warning("No articles passed processing")
                return
            
            # Step 3: Generate summaries for new articles
            await self._generate_summaries(processed_articles)
            
            # Step 4: Save processed articles
            await self._save_articles(processed_articles)
            
            logger.info(f"News task completed: {len(processed_articles)} articles processed")
            
        except Exception as e:
            logger.error(f"Error in scrape_and_process_news task: {e}")
    
    async def _scrape_news(self) -> List[Dict[str, Any]]:
        """Scrape articles from RSS feeds"""
        try:
            logger.info(f"Scraping {len(config.rss_feeds)} RSS feeds")
            
            # Fetch articles from all feeds
            articles = await self.scraper.fetch_all_feeds(config.rss_feeds)
            
            logger.info(f"Scraped {len(articles)} articles from RSS feeds")
            return articles
            
        except Exception as e:
            logger.error(f"Error scraping news: {e}")
            return []
    
    async def _process_articles(self, articles: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process scraped articles"""
        try:
            logger.info(f"Processing {len(articles)} articles")
            
            # Process articles (categorize, filter, etc.)
            processed_articles = await self.processor.process_articles(articles)
            
            # Filter by relevance
            relevant_articles = self.processor.filter_articles_by_relevance(processed_articles, min_score=0.2)
            
            # Sort by relevance
            sorted_articles = self.processor.sort_articles_by_relevance(relevant_articles)
            
            logger.info(f"Processed {len(sorted_articles)} relevant articles")
            return sorted_articles
            
        except Exception as e:
            logger.error(f"Error processing articles: {e}")
            return []
    
    async def _generate_summaries(self, articles: List[Dict[str, Any]]):
        """Generate AI summaries for articles"""
        try:
            # Load existing summaries
            existing_summaries = load_summaries()
            
            # Find articles without summaries
            articles_to_summarize = []
            for article in articles:
                article_id = article.get('id')
                if article_id and article_id not in existing_summaries:
                    articles_to_summarize.append(article)
            
            if not articles_to_summarize:
                logger.info("No new articles to summarize")
                return
            
            logger.info(f"Generating summaries for {len(articles_to_summarize)} articles")
            
            # Generate summaries in batches
            batch_size = 5  # Process in small batches to avoid rate limits
            for i in range(0, len(articles_to_summarize), batch_size):
                batch = articles_to_summarize[i:i + batch_size]
                summaries = await self.llm_service.batch_summarize(batch)
                
                # Save summaries
                if summaries:
                    await self._save_summaries(summaries)
                
                # Small delay between batches
                await asyncio.sleep(2)
            
            logger.info(f"Generated summaries for {len(articles_to_summarize)} articles")
            
        except Exception as e:
            logger.error(f"Error generating summaries: {e}")
    
    async def _save_articles(self, articles: List[Dict[str, Any]]):
        """Save processed articles to storage"""
        try:
            # Load existing articles
            existing_data = load_articles()
            existing_articles = existing_data.get('articles', [])
            
            # Create a set of existing article IDs for quick lookup
            existing_ids = {article.get('id') for article in existing_articles}
            
            # Add new articles
            new_articles = []
            for article in articles:
                if article.get('id') not in existing_ids:
                    new_articles.append(article)
            
            if new_articles:
                # Combine existing and new articles
                all_articles = existing_articles + new_articles
                
                # Sort by publication date (newest first)
                all_articles.sort(
                    key=lambda x: x.get('published_date', ''),
                    reverse=True
                )
                
                # Keep only the latest 1000 articles to prevent storage bloat
                all_articles = all_articles[:1000]
                
                # Save updated articles
                save_articles(all_articles)
                
                logger.info(f"Saved {len(new_articles)} new articles (total: {len(all_articles)})")
            else:
                logger.info("No new articles to save")
                
        except Exception as e:
            logger.error(f"Error saving articles: {e}")
    
    async def _save_summaries(self, summaries: List[Dict[str, Any]]):
        """Save generated summaries"""
        try:
            existing_summaries = load_summaries()
            
            # Add new summaries
            for summary in summaries:
                article_id = summary.get('article_id')
                if article_id:
                    existing_summaries[article_id] = summary
            
            # Save updated summaries
            save_summaries(existing_summaries)
            
            logger.info(f"Saved {len(summaries)} new summaries")
            
        except Exception as e:
            logger.error(f"Error saving summaries: {e}")
    
    async def cleanup_old_data(self):
        """Clean up old articles and summaries"""
        try:
            logger.info("Starting data cleanup task")
            
            # Load current data
            articles_data = load_articles()
            summaries_data = load_summaries()
            
            articles = articles_data.get('articles', [])
            summaries = summaries_data
            
            # Remove articles older than 30 days
            cutoff_date = datetime.now() - timedelta(days=30)
            filtered_articles = []
            removed_count = 0
            
            for article in articles:
                published_date = article.get('published_date')
                if published_date:
                    try:
                        pub_date = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
                        if pub_date > cutoff_date:
                            filtered_articles.append(article)
                        else:
                            removed_count += 1
                    except:
                        # Keep articles with invalid dates
                        filtered_articles.append(article)
                else:
                    # Keep articles without dates
                    filtered_articles.append(article)
            
            # Remove summaries for deleted articles
            article_ids = {article.get('id') for article in filtered_articles}
            filtered_summaries = {
                article_id: summary 
                for article_id, summary in summaries.items() 
                if article_id in article_ids
            }
            
            # Save cleaned data
            articles_data['articles'] = filtered_articles
            save_articles(filtered_articles)
            save_summaries(filtered_summaries)
            
            logger.info(f"Cleanup completed: removed {removed_count} old articles")
            
        except Exception as e:
            logger.error(f"Error in cleanup task: {e}")
    
    async def force_refresh(self):
        """Force a complete refresh of news data"""
        try:
            logger.info("Starting forced news refresh")
            
            # Clear existing data
            save_articles([])
            save_summaries({})
            
            # Run full scraping and processing
            await self.scrape_and_process_news()
            
            logger.info("Forced refresh completed")
            
        except Exception as e:
            logger.error(f"Error in force refresh: {e}")
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get statistics about news data"""
        try:
            articles = load_articles()
            summaries = load_summaries()
            
            total_articles = len(articles.get('articles', []))
            total_summaries = len(summaries)
            
            # Count articles by category
            category_counts = {}
            for article in articles.get('articles', []):
                category = article.get('ai_category', 'uncategorized')
                category_counts[category] = category_counts.get(category, 0) + 1
            
            # Count articles by source
            source_counts = {}
            for article in articles.get('articles', []):
                source = article.get('source', 'unknown')
                source_counts[source] = source_counts.get(source, 0) + 1
            
            return {
                'total_articles': total_articles,
                'total_summaries': total_summaries,
                'category_counts': category_counts,
                'source_counts': source_counts,
                'last_updated': articles.get('last_updated')
            }
            
        except Exception as e:
            logger.error(f"Error getting stats: {e}")
            return {} 