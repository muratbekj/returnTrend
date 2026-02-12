# ReturnTrends

A Telegram bot that aggregates and ranks AI news so you don't have to check multiple sites.

**Try it:** [@returnTrendsBot](https://t.me/returnTrendsBot)

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot |
| `/help` | Show commands |
| `/get_today_news` | Get ranked AI headlines |
| `/latest_summary` | Get a concise AI news summary |

## How it works

1. Scrapes RSS feeds and web pages for AI news
2. Uses an LLM to rank stories by impact and relevance
3. Delivers the top stories to your Telegram chat

## Setup

```bash
git clone <repo-url>
cd returnTrend
uv sync
```

Create a `.env` file:

```
TELEGRAM_BOT_API=your_bot_token
TELEGRAM_BOT_USERNAME=@your_bot_username
```

Run:

```bash
python main.py
```

## Sources

VentureBeat, The Guardian AI, Hugging Face Blog, MIT News, Dev.to, and more.
