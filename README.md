# AI News Bot 🤖📰

An intelligent Telegram bot that scrapes news from RSS feeds and provides AI-generated summaries using OpenAI's GPT models.

## Features

- 📰 **RSS Feed Scraping**: Automatically fetches news from multiple RSS feeds
- 🤖 **AI Summarization**: Uses OpenAI GPT to generate concise summaries
- 🏷️ **Smart Categorization**: Automatically categorizes articles by topic
- 📱 **Telegram Integration**: Full-featured Telegram bot with inline keyboards
- ⚙️ **Personalization**: User preferences and saved articles
- 🔄 **Background Processing**: Automated news scraping and processing
- 📊 **Statistics**: Track user engagement and bot performance

## Quick Start

### Prerequisites

- Python 3.8 or higher
- [uv](https://github.com/astral-sh/uv) package manager
- Telegram Bot Token (from [@BotFather](https://t.me/botfather))
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ai_news_bot
   ```

2. **Install dependencies with uv**
   ```bash
   uv sync
   ```

3. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your API keys and settings
   ```

4. **Configure your bot**
   Edit the `.env` file with your credentials:
   ```env
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=your_openai_api_key_here
   ADMIN_USER_IDS=123456789,987654321
   ```

5. **Run the bot**
   ```bash
   uv run python main.py
   ```

## Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `TELEGRAM_BOT_TOKEN` | Your Telegram bot token | Yes | - |
| `OPENAI_API_KEY` | Your OpenAI API key | Yes | - |
| `ADMIN_USER_IDS` | Comma-separated admin user IDs | No | - |
| `LLM_MODEL` | OpenAI model to use | No | `gpt-3.5-turbo` |
| `SCRAPE_INTERVAL_MINUTES` | RSS scraping interval | No | `30` |
| `MAX_ARTICLES_PER_USER` | Max articles per digest | No | `10` |

### RSS Feeds

The bot comes pre-configured with popular technology RSS feeds:

- TechCrunch
- Ars Technica
- The Verge
- BBC Technology
- Reuters Technology
- Wired
- MIT Technology Review
- VentureBeat

You can modify the feeds in `config.py`.

## Usage

### Bot Commands

- `/start` - Welcome message and introduction
- `/news` - Get latest news digest
- `/categories` - Browse news by category
- `/settings` - Manage your preferences
- `/stats` - View your usage statistics
- `/help` - Show help information

### Admin Commands

- `/admin_stats` - View bot statistics (admin only)
- `/broadcast` - Send message to all users (admin only)

### Features

1. **News Digests**: Get personalized news summaries
2. **Category Filtering**: Browse news by technology, business, science, etc.
3. **Article Saving**: Save interesting articles for later
4. **AI Summaries**: Get concise AI-generated summaries
5. **Key Points**: Extract key points from articles

## Project Structure

```
ai_news_bot/
├── main.py                 # Entry point
├── config.py              # Configuration
├── pyproject.toml         # Dependencies (uv)
├── env.example            # Environment template
├── data/                  # Data storage
│   ├── articles.json      # Scraped articles
│   ├── summaries.json     # AI summaries
│   └── users.json         # User preferences
├── services/              # Core services
│   ├── scraper.py         # RSS scraping
│   ├── llm_service.py     # AI summarization
│   └── news_processor.py  # News processing
├── bot/                   # Telegram bot
│   ├── bot.py            # Main bot logic
│   └── handlers.py        # Command handlers
├── tasks/                 # Background tasks
│   ├── scheduler.py       # Task scheduler
│   └── news_tasks.py      # News tasks
└── utils/                 # Utilities
    ├── storage.py         # Data storage
    └── helpers.py         # Helper functions
```

## Development

### Setting up development environment

```bash
# Install development dependencies
uv sync --group dev

# Run tests
uv run pytest

# Format code
uv run black .

# Type checking
uv run mypy .
```

### Adding new RSS feeds

Edit `config.py` and add new feeds to the `DEFAULT_RSS_FEEDS` list:

```python
RSSFeed("Your Feed", "https://example.com/feed/", "category")
```

### Customizing AI prompts

Modify the prompt templates in `services/llm_service.py` to customize AI behavior.

## Deployment

### Local Development

```bash
uv run python main.py
```

### Production Deployment

1. **Set up a server** (VPS, cloud instance, etc.)
2. **Install Python and uv**
3. **Clone and configure the bot**
4. **Use a process manager** (systemd, supervisor, etc.)
5. **Set up logging and monitoring**

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install uv
RUN uv sync --frozen

CMD ["uv", "run", "python", "main.py"]
```

## Monitoring and Maintenance

### Logs

The bot creates detailed logs in `ai_news_bot.log` with different levels:
- INFO: Normal operations
- WARNING: Non-critical issues
- ERROR: Critical errors

### Data Backup

The bot automatically creates backups in `data/backups/`. You can also manually trigger backups:

```python
from utils.storage import backup_data
backup_data()
```

### Performance Monitoring

Monitor these metrics:
- Articles scraped per day
- Summaries generated
- User engagement
- API usage (OpenAI)

## Troubleshooting

### Common Issues

1. **Bot not responding**
   - Check if the bot token is correct
   - Verify the bot is running
   - Check logs for errors

2. **No articles appearing**
   - Check RSS feed URLs
   - Verify internet connectivity
   - Check OpenAI API key

3. **High API costs**
   - Adjust `SCRAPE_INTERVAL_MINUTES`
   - Limit `MAX_ARTICLES_PER_USER`
   - Use cheaper OpenAI models

### Getting Help

1. Check the logs in `ai_news_bot.log`
2. Verify your environment variables
3. Test RSS feeds manually
4. Check OpenAI API status

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- OpenAI for providing the GPT API
- Telegram for the bot platform
- RSS feed providers for the news content

---

Made with ❤️ and AI 🤖 