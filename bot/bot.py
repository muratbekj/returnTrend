"""
Main Telegram Bot for AI News Bot
"""

import asyncio
import logging
from typing import Optional
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.utils import executor

from config import BotConfig
from .handlers import setup_handlers
from utils.storage import load_articles, load_summaries, save_user_preferences, load_user_preferences

logger = logging.getLogger(__name__)


class NewsBot:
    """Main Telegram bot for AI News Bot"""
    
    def __init__(self, config: Optional[BotConfig] = None):
        if config is None:
            from config import config as app_config
            config = app_config.bot
        
        self.config = config
        self.bot = Bot(token=config.token)
        self.dp = Dispatcher(self.bot, storage=MemoryStorage())
        
        # Setup handlers
        setup_handlers(self.dp)
        
        # Bot state
        self.is_running = False
    
    async def start(self):
        """Start the bot"""
        if self.is_running:
            logger.warning("Bot is already running")
            return
        
        self.is_running = True
        logger.info("Starting Telegram bot...")
        
        try:
            # Start polling
            await self.dp.start_polling()
        except Exception as e:
            logger.error(f"Error starting bot: {e}")
            raise
        finally:
            self.is_running = False
    
    async def stop(self):
        """Stop the bot"""
        if not self.is_running:
            return
        
        logger.info("Stopping Telegram bot...")
        self.is_running = False
        
        # Close bot session
        await self.bot.session.close()
    
    async def send_news_digest(self, user_id: int, articles: list, max_articles: int = 5):
        """Send a news digest to a user"""
        if not articles:
            await self.bot.send_message(
                user_id,
                "No new articles available at the moment. Check back later! 📰"
            )
            return
        
        # Limit number of articles
        articles = articles[:max_articles]
        
        # Send digest header
        await self.bot.send_message(
            user_id,
            f"📰 *Latest News Digest*\n\nHere are the top {len(articles)} articles:",
            parse_mode='Markdown'
        )
        
        # Send each article
        for i, article in enumerate(articles, 1):
            await self._send_article(user_id, article, i)
            await asyncio.sleep(1)  # Avoid rate limiting
    
    async def _send_article(self, user_id: int, article: dict, index: int):
        """Send a single article to a user"""
        title = article.get('title', 'No title')
        link = article.get('link', '')
        source = article.get('source', 'Unknown source')
        category = article.get('ai_category', 'uncategorized')
        
        # Get summary if available
        summary = None
        summaries = load_summaries()
        article_id = article.get('id')
        if article_id and article_id in summaries:
            summary = summaries[article_id].get('summary', '')
        
        # Create message
        message = f"*{index}. {title}*\n\n"
        message += f"📰 Source: {source}\n"
        message += f"🏷️ Category: {category.title()}\n"
        
        if summary:
            # Truncate summary if too long
            if len(summary) > 300:
                summary = summary[:300] + "..."
            message += f"\n📝 Summary: {summary}\n"
        
        message += f"\n🔗 [Read full article]({link})"
        
        # Create inline keyboard for actions
        keyboard = types.InlineKeyboardMarkup(row_width=2)
        keyboard.add(
            types.InlineKeyboardButton("📖 Read", url=link),
            types.InlineKeyboardButton("💾 Save", callback_data=f"save_{article_id}")
        )
        
        try:
            await self.bot.send_message(
                user_id,
                message,
                parse_mode='Markdown',
                disable_web_page_preview=True,
                reply_markup=keyboard
            )
        except Exception as e:
            logger.error(f"Error sending article to user {user_id}: {e}")
            # Fallback without markdown
            fallback_message = f"{index}. {title}\n\nSource: {source}\nCategory: {category}\n\nRead: {link}"
            await self.bot.send_message(user_id, fallback_message)
    
    async def send_error_message(self, user_id: int, error_message: str):
        """Send an error message to a user"""
        await self.bot.send_message(
            user_id,
            f"❌ Error: {error_message}\n\nPlease try again later or contact support."
        )
    
    async def send_admin_message(self, message: str):
        """Send a message to all admin users"""
        for admin_id in self.config.admin_user_ids:
            try:
                await self.bot.send_message(admin_id, f"🔔 Admin: {message}")
            except Exception as e:
                logger.error(f"Error sending admin message to {admin_id}: {e}")
    
    def is_admin(self, user_id: int) -> bool:
        """Check if a user is an admin"""
        return user_id in self.config.admin_user_ids 