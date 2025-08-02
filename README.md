# ReturnTrends AI News Bot 🤖

A Telegram bot that aggregates AI news from multiple sources so you can stay updated without visiting each website individually.

**Try it now: [@returnTrendsBot](https://t.me/returnTrendsBot)**

## What it does

This bot scrapes news from various AI-focused RSS feeds and websites, then provides you with:
- **Today's headlines** - Get a quick overview of the latest AI news
- **AI-generated summaries** - Get intelligent summaries of the articles
- **Direct links** - Access the full articles when you want to dive deeper

## Features

- 📰 **News Aggregation**: Collects articles from multiple AI news sources
- 🤖 **AI Summaries**: Uses LLM to generate intelligent summaries
- 📱 **Telegram Integration**: Easy to use through Telegram chat
- ⚡ **Real-time Updates**: Get the latest news as it happens

## Available Commands

- `/start` - Start the bot and get a welcome message
- `/help` - Show available commands
- `/get_today_news` - Get today's AI news headlines
- `/latest_summary` - Get AI-generated summaries of the latest articles

## News Sources

The bot currently scrapes from:
- Data Machina
- OpenAI News
- The Verge
- The Decoder
- Techspot

## Setup

1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up your environment variables:
   - `TELEGRAM_BOT_API` - Your Telegram bot token
   - `TELEGRAM_BOT_USERNAME` - Your bot's username
4. Run the bot: `python main.py`

## Why I built this

I got tired of visiting multiple websites to stay updated on AI news. This bot brings all the important AI news to one place - my Telegram chat. Now I can quickly scan headlines and get summaries without the hassle of opening multiple tabs and websites.

Perfect for staying informed about AI developments without the information overload! 🚀
