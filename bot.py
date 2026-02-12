import os
import re
import time
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from services.scraper import SimpleWebScraper
from services.llm import SimpleLLMConnector

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME')
TELEGRAM_MESSAGE_LIMIT = 4000
NEWS_COMMAND_COOLDOWN_SECONDS = int(os.getenv("NEWS_COMMAND_COOLDOWN_SECONDS", "90"))
SUMMARY_COMMAND_COOLDOWN_SECONDS = int(os.getenv("SUMMARY_COMMAND_COOLDOWN_SECONDS", "180"))
_LAST_COMMAND_CALL = {}


def _format_published_at(raw_published_at: str) -> str:
    """Format ISO date into a short readable UTC date."""
    if not raw_published_at:
        return ""


def _get_cooldown_remaining(update: Update, command_name: str, cooldown_seconds: int) -> int:
    """Return remaining cooldown seconds for this user+command (0 when allowed)."""
    user = update.effective_user
    if not user:
        return 0

    key = (user.id, command_name)
    now = time.monotonic()
    last_called = _LAST_COMMAND_CALL.get(key)
    if last_called is None:
        _LAST_COMMAND_CALL[key] = now
        return 0

    elapsed = now - last_called
    remaining = cooldown_seconds - elapsed
    if remaining > 0:
        return int(remaining) + 1

    _LAST_COMMAND_CALL[key] = now
    return 0
    try:
        published_dt = datetime.fromisoformat(raw_published_at)
        return published_dt.strftime("%b %d, %Y")
    except Exception:
        return ""


def _clean_text(text: str, preserve_line_breaks: bool = False) -> str:
    """Normalize text coming from feeds/LLM for nicer Telegram output."""
    if not text:
        return ""
    # Remove HTML tags and normalize whitespace.
    text = re.sub(r"<[^>]+>", "", text)
    # Remove common markdown formatting and convert markdown links.
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1 (\2)", text)  # [text](url)
    text = re.sub(r"^\s{0,3}#{1,6}\s*", "", text, flags=re.MULTILINE)  # headings
    text = re.sub(r"(\*\*|__)(.*?)\1", r"\2", text)  # bold
    text = re.sub(r"(?<!\*)\*(?!\*)(.*?)\*(?<!\*)", r"\1", text)  # italic *
    text = re.sub(r"(?<!_)_(?!_)(.*?)_(?<!_)", r"\1", text)  # italic _
    text = re.sub(r"`([^`]+)`", r"\1", text)  # inline code
    text = re.sub(r"^\s*>\s*", "", text, flags=re.MULTILINE)  # blockquote marker

    if preserve_line_breaks:
        lines = [re.sub(r"[ \t]+", " ", line).strip() for line in text.splitlines()]
        text = "\n".join(lines)
        text = re.sub(r"\n{3,}", "\n\n", text).strip()
        return text

    text = re.sub(r"\s+", " ", text).strip()
    return text


async def _send_long_message(update: Update, text: str) -> None:
    """Send Telegram-safe message chunks when content is too long."""
    if len(text) <= TELEGRAM_MESSAGE_LIMIT:
        await update.message.reply_text(text)
        return

    current_chunk = ""
    for paragraph in text.split("\n\n"):
        candidate = f"{current_chunk}\n\n{paragraph}".strip() if current_chunk else paragraph
        if len(candidate) > TELEGRAM_MESSAGE_LIMIT:
            if current_chunk:
                await update.message.reply_text(current_chunk)
                current_chunk = paragraph
            else:
                # Fallback for very long single paragraph.
                for i in range(0, len(paragraph), TELEGRAM_MESSAGE_LIMIT):
                    await update.message.reply_text(paragraph[i:i + TELEGRAM_MESSAGE_LIMIT])
                current_chunk = ""
        else:
            current_chunk = candidate

    if current_chunk:
        await update.message.reply_text(current_chunk)

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.message.from_user.username} started the bot")
    await update.message.reply_text(
        "Hi! I am ReturnTrends.\n"
        "I track AI news and can share:\n"
        "- fresh headlines\n"
        "- a concise daily summary\n\n"
        "Type /help to see all commands."
    )

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.message.from_user.username} requested help")
    await update.message.reply_text(
        "Available commands:\n"
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "/get_today_news - Get today's AI headlines\n"
        "/latest_summary - Get a concise AI news summary"
    )

async def get_today_news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.message.from_user.username} requested today's news")
    remaining = _get_cooldown_remaining(update, "get_today_news", NEWS_COMMAND_COOLDOWN_SECONDS)
    if remaining > 0:
        await update.message.reply_text(
            f"Please wait {remaining}s before using /get_today_news again."
        )
        return

    try:
        scraper = SimpleWebScraper()
        articles = scraper.get_all_articles()
        
        if not articles:
            await update.message.reply_text("No articles found at the moment. Please try again later.")
            return
        
        llm = SimpleLLMConnector()
        ranked_articles = llm.rank_articles(articles, top_n=10)
        max_items = len(ranked_articles)
        today_label = datetime.now().strftime("%b %d, %Y")
        await update.message.reply_text(
            f"AI News Briefing - {today_label}\n"
            f"Showing {max_items} LLM-ranked stories by expected impact:"
        )
        
        for i, (title, details) in enumerate(ranked_articles.items(), 1):
            source = _clean_text(details.get('source', 'Unknown source'))
            summary = _clean_text(details.get('summary', 'No summary available'))
            title = _clean_text(title)
            link = details.get('link', '')
            published_at = _format_published_at(details.get('published_at', ''))
            judge_score = details.get('judge_score', 5)
            judge_reason = _clean_text(details.get('judge_reason', 'Relevant update worth tracking'))
            
            article_message = f"Story {i}/{max_items}\n"
            article_message += f"Headline: {title}\n"
            article_message += f"Impact score: {judge_score}/10\n"
            article_message += f"Judge note: {judge_reason}\n"
            article_message += f"Source: {source}\n"
            if published_at:
                article_message += f"Published: {published_at}\n"
            if summary:
                summary_text = summary[:220]
                if len(summary) > 220:
                    summary_text += "..."
                article_message += f"Why it matters: {summary_text}\n"
            if link:
                article_message += f"Read more: {link}\n"
            
            # Limit to first 10 articles to avoid message length limits
            await _send_long_message(update, article_message.strip())
        
    except Exception as e:
        print(f"Error in get_today_news_cmd: {e}")
        await update.message.reply_text("Sorry, there was an error fetching the news. Please try again later.")

async def latest_summary_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"User {update.message.from_user.username} requested latest summary")
    remaining = _get_cooldown_remaining(update, "latest_summary", SUMMARY_COMMAND_COOLDOWN_SECONDS)
    if remaining > 0:
        await update.message.reply_text(
            f"Please wait {remaining}s before using /latest_summary again."
        )
        return

    try:
        scraper = SimpleWebScraper()
        articles = scraper.get_all_articles()

        if not articles:
            await update.message.reply_text("No articles found right now. Try again in a few minutes.")
            return

        llm = SimpleLLMConnector()
        ranked_articles = llm.rank_articles(articles, top_n=12)
        llm_response = _clean_text(llm.process_articles(ranked_articles), preserve_line_breaks=True)
        final_response = (
            "Daily AI news summary:\n\n"
            f"{llm_response}" if llm_response else
            "Daily AI news summary:\n\nI could not generate a summary this time."
        )
        await _send_long_message(update, final_response)
    except Exception as e:
        print(f"Error in latest_summary_cmd: {e}")
        await update.message.reply_text("Sorry, I could not generate the summary right now. Please try again later.")

def handle_response(text: str) -> str:
    """Handle user messages and return appropriate responses"""
    processed: str = text.lower()
    
    if 'hello' in processed:
        return "Hey! If you want the latest AI updates, try /get_today_news or /latest_summary."
    
    if 'how are you' in processed:
        return "Doing great and ready to fetch AI news for you."
    
    if 'bye' in processed:
        return "See you soon. Come back anytime for fresh AI updates."
    
    if 'news' in processed:
        return 'I can help you get the latest news! Use /get_today_news to see today\'s headlines or /latest_summary for a comprehensive summary.'
    
    if 'summary' in processed:
        return "Use /latest_summary for a concise overview of today's most relevant stories."
    
    return "I did not understand that yet. Use /help to see available commands."

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
    await update.message.reply_text(response)

