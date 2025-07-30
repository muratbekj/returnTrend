import os, logging
from telegram import Update
from telegram.ext import ContextTypes
from services.scraper import SimpleWebScraper
from services.llm import SimpleLLMConnector

from dotenv import load_dotenv

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

load_dotenv()

TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME')

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} started the bot")
    await update.message.reply_text("Hello! I'm returntrends bot. How can I help you today?")

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} requested help")
    await update.message.reply_text("""
    /start - Start the bot
    /help - Show this help message
    /get_today_news - Get the latest news
    /latest_summary - Get the latest news summarized
    """)

async def get_today_news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} requested today's news")
    try:
        scraper = SimpleWebScraper()
        articles = scraper.get_all_articles()
        
        if not articles:
            await update.message.reply_text("No articles found at the moment. Please try again later.")
            return
        
        # Format articles as a readable string
        formatted_articles = "📰 Today's AI News Headlines:\n\n"
        
        for i, (title, details) in enumerate(articles.items(), 1):
            source = details.get('source', 'Unknown Source')
            summary = details.get('summary', 'No summary available')
            link = details.get('link', '')
            
            formatted_articles += f"{i}. {title}\n"
            formatted_articles += f"   Source: {source}\n"
            formatted_articles += f"   {summary[:150]}...\n"
            if link:
                formatted_articles += f"   Link: {link}\n"
            formatted_articles += "\n"
            
            # Limit to first 10 articles to avoid message length limits
            if i >= 10:
                break
        
        await update.message.reply_text(formatted_articles)
        
    except Exception as e:
        print(f"Error in get_today_news_cmd: {e}")
        await update.message.reply_text("Sorry, there was an error fetching the news. Please try again later.")

async def latest_summary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.info(f"User {update.message.from_user.username} requested latest summary")
    scraper = SimpleWebScraper()
    articles = scraper.get_all_articles()
    llm = SimpleLLMConnector()
    llm_response = llm.process_articles(articles)
    await update.message.reply_text(llm_response)

def handle_response(text: str) -> str:
    """Handle user messages and return appropriate responses"""
    processed: str = text.lower()
    
    if 'hello' in processed:
        return 'Hey there!'
    
    if 'how are you' in processed:
        return 'I am good!'
    
    if 'bye' in processed:
        return 'Talk to you later!'
    
    if 'news' in processed:
        return 'I can help you get the latest news! Use /get_today_news to see today\'s headlines or /latest_summary for a comprehensive summary.'
    
    if 'summary' in processed:
        return 'Use /latest_summary to get the most recent summarized articles!'
    
    return 'I don\'t understand that. Try /help for available commands.'

# Responses
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_type: str = update.message.chat.type
    text: str = update.message.text

    if message_type == 'group':
        if TELEGRAM_BOT_USERNAME in text:
            new_text: str = text.replace(TELEGRAM_BOT_USERNAME, '').strip()
            response: str = handle_response(new_text)
        else:
            return
    else:
        response: str = handle_response(text)
    
    logger.info(f"Bot response: {response}")
    await update.message.reply_text(response)

