"""
Configuration settings for AI News Bot
"""

import os
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class RSSFeed:
    """RSS feed configuration"""
    name: str
    url: str
    category: str
    enabled: bool = True

@dataclass
class BotConfig:
    """Bot configuration"""
    token: str
    admin_user_ids: List[int]
    max_articles_per_user: int = 10
    summary_max_length: int = 500

@dataclass
class LLMConfig:
    """LLM service configuration"""
    api_key: str
    model: str = "gpt-3.5-turbo"
    max_tokens: int = 1000
    temperature: float = 0.7

@dataclass
class AppConfig:
    """Main application configuration"""
    bot: BotConfig
    llm: LLMConfig
    rss_feeds: List[RSSFeed]
    scrape_interval_minutes: int = 30
    data_dir: str = "data"

# Default RSS feeds
DEFAULT_RSS_FEEDS = [
    RSSFeed("TechCrunch", "https://techcrunch.com/feed/", "technology"),
    RSSFeed("Ars Technica", "https://feeds.arstechnica.com/arstechnica/index", "technology"),
    RSSFeed("The Verge", "https://www.theverge.com/rss/index.xml", "technology"),
    RSSFeed("BBC Technology", "https://feeds.bbci.co.uk/news/technology/rss.xml", "technology"),
    RSSFeed("Reuters Technology", "https://feeds.reuters.com/reuters/technologyNews", "technology"),
    RSSFeed("Wired", "https://www.wired.com/feed/rss", "technology"),
    RSSFeed("MIT Technology Review", "https://www.technologyreview.com/feed/", "technology"),
    RSSFeed("VentureBeat", "https://venturebeat.com/feed/", "technology"),
]

def load_config() -> AppConfig:
    """Load configuration from environment variables and defaults"""
    
    # Bot configuration
    bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not bot_token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    admin_user_ids = []
    admin_ids_str = os.getenv("ADMIN_USER_IDS", "")
    if admin_ids_str:
        admin_user_ids = [int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()]
    
    bot_config = BotConfig(
        token=bot_token,
        admin_user_ids=admin_user_ids,
        max_articles_per_user=int(os.getenv("MAX_ARTICLES_PER_USER", "10")),
        summary_max_length=int(os.getenv("SUMMARY_MAX_LENGTH", "500"))
    )
    
    # LLM configuration
    llm_api_key = os.getenv("OPENAI_API_KEY")
    if not llm_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")
    
    llm_config = LLMConfig(
        api_key=llm_api_key,
        model=os.getenv("LLM_MODEL", "gpt-3.5-turbo"),
        max_tokens=int(os.getenv("LLM_MAX_TOKENS", "1000")),
        temperature=float(os.getenv("LLM_TEMPERATURE", "0.7"))
    )
    
    # RSS feeds - can be overridden via environment
    rss_feeds = DEFAULT_RSS_FEEDS
    
    # App configuration
    app_config = AppConfig(
        bot=bot_config,
        llm=llm_config,
        rss_feeds=rss_feeds,
        scrape_interval_minutes=int(os.getenv("SCRAPE_INTERVAL_MINUTES", "30")),
        data_dir=os.getenv("DATA_DIR", "data")
    )
    
    return app_config

# Global config instance
config = load_config() 