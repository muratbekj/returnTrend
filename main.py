#!/usr/bin/env python3
"""
AI News Bot - Main Entry Point
A Telegram bot that scrapes news and provides AI-generated summaries.
"""

import os

from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot import start_cmd, help_cmd, get_today_news_cmd, latest_summary_cmd, handle_message

from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_API')
TELEGRAM_BOT_USERNAME = os.getenv('TELEGRAM_BOT_USERNAME')

def main():
    """Main application entry point."""
    print("Starting returntrends bot...")
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    # CMD handlers
    application.add_handler(CommandHandler("start", start_cmd))
    application.add_handler(CommandHandler("help", help_cmd))
    application.add_handler(CommandHandler("get_today_news", get_today_news_cmd))
    application.add_handler(CommandHandler("latest_summary", latest_summary_cmd))
    # Message handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.run_polling(poll_interval=5)

if __name__ == "__main__":
    main()
