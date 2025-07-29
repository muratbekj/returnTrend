"""
Telegram Bot Command Handlers
"""

import logging
from typing import List, Dict, Any
from aiogram import Dispatcher, types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

from config import config
from utils.storage import load_articles, load_summaries, save_user_preferences, load_user_preferences
from services.news_processor import NewsProcessor

logger = logging.getLogger(__name__)


class UserStates(StatesGroup):
    """User interaction states"""
    waiting_for_category = State()
    waiting_for_feedback = State()


def setup_handlers(dp: Dispatcher):
    """Setup all bot command handlers"""
    
    # Basic commands
    dp.register_message_handler(cmd_start, commands=['start'])
    dp.register_message_handler(cmd_help, commands=['help'])
    dp.register_message_handler(cmd_news, commands=['news'])
    dp.register_message_handler(cmd_categories, commands=['categories'])
    dp.register_message_handler(cmd_settings, commands=['settings'])
    dp.register_message_handler(cmd_stats, commands=['stats'])
    
    # Admin commands
    dp.register_message_handler(cmd_admin_stats, commands=['admin_stats'])
    dp.register_message_handler(cmd_admin_broadcast, commands=['broadcast'])
    
    # Callback queries
    dp.register_callback_query_handler(handle_category_selection, lambda c: c.data.startswith('category_'))
    dp.register_callback_query_handler(handle_save_article, lambda c: c.data.startswith('save_'))
    dp.register_callback_query_handler(handle_feedback, lambda c: c.data.startswith('feedback_'))
    
    # Text handlers
    dp.register_message_handler(handle_text, content_types=['text'])


async def cmd_start(message: types.Message):
    """Handle /start command"""
    user_id = message.from_user.id
    user_name = message.from_user.first_name
    
    welcome_message = f"""
🤖 Welcome to AI News Bot, {user_name}!

I'm your personal AI-powered news assistant. Here's what I can do:

📰 Get the latest news from top tech sources
🤖 AI-generated summaries and key points
🏷️ Smart categorization of articles
⚙️ Personalized news preferences

**Commands:**
/start - Show this welcome message
/news - Get latest news digest
/categories - Browse news by category
/settings - Manage your preferences
/help - Show help information

**Quick Start:**
Send /news to get the latest technology news with AI summaries!

Made with ❤️ and AI
    """
    
    await message.answer(welcome_message, parse_mode='Markdown')


async def cmd_help(message: types.Message):
    """Handle /help command"""
    help_message = """
📚 **AI News Bot Help**

**Available Commands:**
/start - Welcome message and introduction
/news - Get latest news digest (default: technology)
/categories - Browse news by category
/settings - Manage your preferences
/stats - View your usage statistics
/help - Show this help message

**Admin Commands:**
/admin_stats - View bot statistics (admin only)
/broadcast - Send message to all users (admin only)

**Features:**
• AI-powered article summarization
• Smart categorization
• Personalized news preferences
• Save interesting articles
• Multiple news sources

**Tips:**
• Use /news to get started
• Try different categories with /categories
• Save articles you like for later reference
• Adjust settings to personalize your experience

Need help? Contact the bot administrator.
    """
    
    await message.answer(help_message, parse_mode='Markdown')


async def cmd_news(message: types.Message):
    """Handle /news command"""
    user_id = message.from_user.id
    
    try:
        # Load articles
        articles = load_articles()
        if not articles:
            await message.answer("📰 No articles available at the moment. Please try again later!")
            return
        
        # Get user preferences
        user_prefs = load_user_preferences(user_id)
        category = user_prefs.get('preferred_category', 'technology')
        
        # Filter articles by category
        processor = NewsProcessor(config.llm)
        category_articles = processor.filter_articles_by_category(articles, category)
        
        if not category_articles:
            # Fallback to all articles
            category_articles = articles
        
        # Sort by relevance and limit
        sorted_articles = processor.sort_articles_by_relevance(category_articles)
        max_articles = config.bot.max_articles_per_user
        
        await send_news_digest(message, sorted_articles[:max_articles])
        
    except Exception as e:
        logger.error(f"Error in cmd_news: {e}")
        await message.answer("❌ Sorry, there was an error fetching news. Please try again later.")


async def cmd_categories(message: types.Message):
    """Handle /categories command"""
    categories = [
        ('technology', '🤖 Technology'),
        ('business', '💼 Business'),
        ('science', '🔬 Science'),
        ('politics', '🏛️ Politics'),
        ('entertainment', '🎬 Entertainment'),
        ('sports', '⚽ Sports'),
        ('health', '🏥 Health'),
        ('environment', '🌍 Environment'),
        ('other', '📰 Other')
    ]
    
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    for category, label in categories:
        keyboard.add(types.InlineKeyboardButton(label, callback_data=f"category_{category}"))
    
    await message.answer(
        "🏷️ **Select a news category:**\n\nChoose a category to browse articles:",
        parse_mode='Markdown',
        reply_markup=keyboard
    )


async def cmd_settings(message: types.Message):
    """Handle /settings command"""
    user_id = message.from_user.id
    user_prefs = load_user_preferences(user_id)
    
    preferred_category = user_prefs.get('preferred_category', 'technology')
    max_articles = user_prefs.get('max_articles', config.bot.max_articles_per_user)
    
    settings_message = f"""
⚙️ **Your Settings**

**Preferred Category:** {preferred_category.title()}
**Max Articles per Digest:** {max_articles}
**Summary Length:** {config.bot.summary_max_length} characters

**Available Categories:**
• Technology (default)
• Business
• Science
• Politics
• Entertainment
• Sports
• Health
• Environment
• Other

Use /categories to change your preferred category.
    """
    
    await message.answer(settings_message, parse_mode='Markdown')


async def cmd_stats(message: types.Message):
    """Handle /stats command"""
    user_id = message.from_user.id
    user_prefs = load_user_preferences(user_id)
    
    articles_read = user_prefs.get('articles_read', 0)
    articles_saved = user_prefs.get('articles_saved', 0)
    last_active = user_prefs.get('last_active', 'Never')
    
    stats_message = f"""
📊 **Your Statistics**

**Articles Read:** {articles_read}
**Articles Saved:** {articles_saved}
**Last Active:** {last_active}
**Preferred Category:** {user_prefs.get('preferred_category', 'technology').title()}

Keep reading to see your stats grow! 📈
    """
    
    await message.answer(stats_message, parse_mode='Markdown')


async def cmd_admin_stats(message: types.Message):
    """Handle /admin_stats command (admin only)"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ This command is only available to administrators.")
        return
    
    try:
        articles = load_articles()
        summaries = load_summaries()
        
        stats_message = f"""
🔧 **Admin Statistics**

**Total Articles:** {len(articles)}
**Total Summaries:** {len(summaries)}
**Last Update:** {articles.get('last_updated', 'Unknown')}

**Articles by Category:**
"""
        
        # Count articles by category
        category_counts = {}
        for article in articles.get('articles', []):
            category = article.get('ai_category', 'uncategorized')
            category_counts[category] = category_counts.get(category, 0) + 1
        
        for category, count in sorted(category_counts.items()):
            stats_message += f"• {category.title()}: {count}\n"
        
        await message.answer(stats_message, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Error in admin_stats: {e}")
        await message.answer("❌ Error fetching admin statistics.")


async def cmd_admin_broadcast(message: types.Message):
    """Handle /broadcast command (admin only)"""
    user_id = message.from_user.id
    
    if not is_admin(user_id):
        await message.answer("❌ This command is only available to administrators.")
        return
    
    # Extract broadcast message
    broadcast_text = message.text.replace('/broadcast', '').strip()
    
    if not broadcast_text:
        await message.answer("❌ Please provide a message to broadcast.\nUsage: /broadcast Your message here")
        return
    
    await message.answer(f"📢 Broadcasting message to all users...\n\nMessage: {broadcast_text}")
    
    # TODO: Implement actual broadcast functionality
    # This would require storing user IDs and sending messages to all users


async def handle_category_selection(callback_query: types.CallbackQuery):
    """Handle category selection from inline keyboard"""
    user_id = callback_query.from_user.id
    category = callback_query.data.replace('category_', '')
    
    try:
        # Update user preferences
        user_prefs = load_user_preferences(user_id)
        user_prefs['preferred_category'] = category
        save_user_preferences(user_id, user_prefs)
        
        # Load articles for selected category
        articles = load_articles()
        if not articles:
            await callback_query.message.answer("📰 No articles available for this category.")
            return
        
        # Filter and send articles
        processor = NewsProcessor(config.llm)
        category_articles = processor.filter_articles_by_category(articles, category)
        
        if not category_articles:
            await callback_query.message.answer(f"📰 No articles found in the {category} category.")
            return
        
        sorted_articles = processor.sort_articles_by_relevance(category_articles)
        max_articles = config.bot.max_articles_per_user
        
        await send_news_digest(callback_query.message, sorted_articles[:max_articles])
        
        # Answer callback query
        await callback_query.answer(f"Showing {category} news")
        
    except Exception as e:
        logger.error(f"Error in category selection: {e}")
        await callback_query.answer("❌ Error loading category")


async def handle_save_article(callback_query: types.CallbackQuery):
    """Handle save article callback"""
    user_id = callback_query.from_user.id
    article_id = callback_query.data.replace('save_', '')
    
    try:
        # Update user preferences
        user_prefs = load_user_preferences(user_id)
        saved_articles = user_prefs.get('saved_articles', [])
        
        if article_id not in saved_articles:
            saved_articles.append(article_id)
            user_prefs['saved_articles'] = saved_articles
            user_prefs['articles_saved'] = user_prefs.get('articles_saved', 0) + 1
            save_user_preferences(user_id, user_prefs)
            
            await callback_query.answer("✅ Article saved!")
        else:
            await callback_query.answer("📝 Article already saved")
            
    except Exception as e:
        logger.error(f"Error saving article: {e}")
        await callback_query.answer("❌ Error saving article")


async def handle_feedback(callback_query: types.CallbackQuery):
    """Handle feedback callback"""
    feedback_type = callback_query.data.replace('feedback_', '')
    
    if feedback_type == 'good':
        await callback_query.answer("👍 Thanks for your feedback!")
    elif feedback_type == 'bad':
        await callback_query.answer("👎 We'll work to improve!")
    else:
        await callback_query.answer("📝 Feedback received")


async def handle_text(message: types.Message):
    """Handle text messages"""
    text = message.text.lower().strip()
    
    if text in ['news', 'latest', 'update']:
        await cmd_news(message)
    elif text in ['help', 'commands']:
        await cmd_help(message)
    elif text in ['categories', 'category']:
        await cmd_categories(message)
    elif text in ['settings', 'preferences']:
        await cmd_settings(message)
    elif text in ['stats', 'statistics']:
        await cmd_stats(message)
    else:
        await message.answer(
            "🤖 I didn't understand that. Try /help to see available commands!"
        )


async def send_news_digest(message: types.Message, articles: List[Dict[str, Any]]):
    """Send a news digest to the user"""
    if not articles:
        await message.answer("📰 No articles available at the moment. Check back later!")
        return
    
    # Send digest header
    await message.answer(
        f"📰 *Latest News Digest*\n\nHere are the top {len(articles)} articles:",
        parse_mode='Markdown'
    )
    
    # Send each article
    for i, article in enumerate(articles, 1):
        await send_single_article(message, article, i)


async def send_single_article(message: types.Message, article: Dict[str, Any], index: int):
    """Send a single article"""
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
    message_text = f"*{index}. {title}*\n\n"
    message_text += f"📰 Source: {source}\n"
    message_text += f"🏷️ Category: {category.title()}\n"
    
    if summary:
        if len(summary) > 300:
            summary = summary[:300] + "..."
        message_text += f"\n📝 Summary: {summary}\n"
    
    message_text += f"\n🔗 [Read full article]({link})"
    
    # Create inline keyboard
    keyboard = types.InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        types.InlineKeyboardButton("📖 Read", url=link),
        types.InlineKeyboardButton("💾 Save", callback_data=f"save_{article_id}")
    )
    
    try:
        await message.answer(
            message_text,
            parse_mode='Markdown',
            disable_web_page_preview=True,
            reply_markup=keyboard
        )
    except Exception as e:
        logger.error(f"Error sending article: {e}")
        # Fallback without markdown
        fallback_text = f"{index}. {title}\n\nSource: {source}\nCategory: {category}\n\nRead: {link}"
        await message.answer(fallback_text)


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in config.bot.admin_user_ids 