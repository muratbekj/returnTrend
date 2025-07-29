#!/usr/bin/env python3
"""
AI News Bot - Main Entry Point
A Telegram bot that scrapes news from RSS feeds and provides AI-generated summaries.
"""

import asyncio
import logging
from pathlib import Path

from bot.bot import NewsBot
from tasks.scheduler import TaskScheduler
from utils.storage import ensure_data_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ai_news_bot.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


async def main():
    """Main application entry point."""
    try:
        # Ensure data directories exist
        ensure_data_directories()
        
        # Initialize and start the bot
        bot = NewsBot()
        
        # Initialize task scheduler
        scheduler = TaskScheduler()
        
        # Start background tasks
        scheduler.start()
        
        logger.info("Starting AI News Bot...")
        
        # Start the bot
        await bot.start()
        
    except KeyboardInterrupt:
        logger.info("Shutting down AI News Bot...")
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
        raise
    finally:
        # Cleanup
        if 'scheduler' in locals():
            scheduler.stop()


if __name__ == "__main__":
    asyncio.run(main()) 