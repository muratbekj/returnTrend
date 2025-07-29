"""
Telegram Bot package for AI News Bot
"""

from .bot import NewsBot
from .handlers import setup_handlers

__all__ = ['NewsBot', 'setup_handlers'] 