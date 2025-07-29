"""
Helper functions for AI News Bot
"""

import re
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from urllib.parse import urlparse, quote

logger = logging.getLogger(__name__)


def format_article(article: Dict[str, Any], include_summary: bool = True) -> str:
    """Format an article for display"""
    title = article.get('title', 'No title')
    link = article.get('link', '')
    source = article.get('source', 'Unknown source')
    category = article.get('ai_category', 'uncategorized')
    
    # Format the article
    formatted = f"📰 **{title}**\n\n"
    formatted += f"🔗 Source: {source}\n"
    formatted += f"🏷️ Category: {category.title()}\n"
    
    # Add publication date if available
    published_date = article.get('published_date')
    if published_date:
        try:
            date_obj = datetime.fromisoformat(published_date.replace('Z', '+00:00'))
            formatted += f"📅 Published: {date_obj.strftime('%Y-%m-%d %H:%M')}\n"
        except:
            pass
    
    # Add summary if requested and available
    if include_summary:
        summary = article.get('summary', '')
        if summary:
            # Truncate summary if too long
            if len(summary) > 300:
                summary = summary[:300] + "..."
            formatted += f"\n📝 **Summary:** {summary}\n"
    
    # Add key points if available
    key_points = article.get('key_points', [])
    if key_points:
        formatted += "\n🔑 **Key Points:**\n"
        for point in key_points[:3]:  # Limit to 3 key points
            formatted += f"• {point}\n"
    
    formatted += f"\n🔗 [Read full article]({link})"
    
    return formatted


def truncate_text(text: str, max_length: int = 300, suffix: str = "...") -> str:
    """Truncate text to a maximum length"""
    if len(text) <= max_length:
        return text
    
    # Try to truncate at word boundary
    truncated = text[:max_length - len(suffix)]
    last_space = truncated.rfind(' ')
    
    if last_space > max_length * 0.8:  # If we can find a space in the last 20%
        truncated = truncated[:last_space]
    
    return truncated + suffix


def sanitize_filename(filename: str) -> str:
    """Sanitize a filename for safe file system use"""
    # Remove or replace problematic characters
    sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Remove leading/trailing spaces and dots
    sanitized = sanitized.strip(' .')
    
    # Limit length
    if len(sanitized) > 200:
        sanitized = sanitized[:200]
    
    return sanitized


def extract_domain(url: str) -> str:
    """Extract domain from URL"""
    try:
        parsed = urlparse(url)
        return parsed.netloc.lower()
    except:
        return "unknown"


def is_valid_url(url: str) -> bool:
    """Check if a URL is valid"""
    try:
        parsed = urlparse(url)
        return bool(parsed.scheme and parsed.netloc)
    except:
        return False


def format_timestamp(timestamp: str) -> str:
    """Format a timestamp for display"""
    try:
        if timestamp.endswith('Z'):
            timestamp = timestamp[:-1] + '+00:00'
        
        date_obj = datetime.fromisoformat(timestamp)
        now = datetime.now(date_obj.tzinfo)
        
        # Calculate time difference
        diff = now - date_obj
        
        if diff.days > 0:
            if diff.days == 1:
                return "1 day ago"
            elif diff.days < 7:
                return f"{diff.days} days ago"
            else:
                return date_obj.strftime('%Y-%m-%d')
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            if hours == 1:
                return "1 hour ago"
            else:
                return f"{hours} hours ago"
        elif diff.seconds > 60:
            minutes = diff.seconds // 60
            if minutes == 1:
                return "1 minute ago"
            else:
                return f"{minutes} minutes ago"
        else:
            return "Just now"
            
    except Exception as e:
        logger.warning(f"Error formatting timestamp {timestamp}: {e}")
        return "Unknown time"


def clean_html_tags(text: str) -> str:
    """Remove HTML tags from text"""
    if not text:
        return ""
    
    # Simple HTML tag removal
    clean = re.sub(r'<[^>]+>', '', text)
    
    # Decode common HTML entities
    clean = clean.replace('&amp;', '&')
    clean = clean.replace('&lt;', '<')
    clean = clean.replace('&gt;', '>')
    clean = clean.replace('&quot;', '"')
    clean = clean.replace('&#39;', "'")
    clean = clean.replace('&nbsp;', ' ')
    
    # Remove extra whitespace
    clean = re.sub(r'\s+', ' ', clean).strip()
    
    return clean


def calculate_reading_time(text: str, words_per_minute: int = 200) -> int:
    """Calculate estimated reading time in minutes"""
    if not text:
        return 0
    
    # Count words (simple approach)
    words = len(text.split())
    
    # Calculate reading time
    reading_time = max(1, words // words_per_minute)
    
    return reading_time


def extract_keywords(text: str, max_keywords: int = 10) -> list:
    """Extract keywords from text"""
    if not text:
        return []
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
        'should', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Extract words
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    
    # Filter out stop words and count frequency
    word_freq = {}
    for word in words:
        if word not in stop_words:
            word_freq[word] = word_freq.get(word, 0) + 1
    
    # Sort by frequency and return top keywords
    sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, freq in sorted_words[:max_keywords]]
    
    return keywords


def validate_article_data(article: Dict[str, Any]) -> bool:
    """Validate article data structure"""
    required_fields = ['title', 'link']
    
    for field in required_fields:
        if not article.get(field):
            return False
    
    # Validate URL
    if not is_valid_url(article['link']):
        return False
    
    # Validate title length
    if len(article['title']) < 5 or len(article['title']) > 500:
        return False
    
    return True


def merge_articles(existing_articles: list, new_articles: list) -> list:
    """Merge new articles with existing ones, avoiding duplicates"""
    if not existing_articles:
        return new_articles
    
    if not new_articles:
        return existing_articles
    
    # Create a set of existing article IDs
    existing_ids = {article.get('id') for article in existing_articles if article.get('id')}
    
    # Add new articles that don't exist
    merged = existing_articles.copy()
    for article in new_articles:
        if article.get('id') not in existing_ids:
            merged.append(article)
    
    # Sort by publication date (newest first)
    merged.sort(
        key=lambda x: x.get('published_date', ''),
        reverse=True
    )
    
    return merged


def format_category_name(category: str) -> str:
    """Format category name for display"""
    category_map = {
        'technology': 'Technology',
        'business': 'Business',
        'science': 'Science',
        'politics': 'Politics',
        'entertainment': 'Entertainment',
        'sports': 'Sports',
        'health': 'Health',
        'environment': 'Environment',
        'other': 'Other'
    }
    
    return category_map.get(category.lower(), category.title())


def get_emoji_for_category(category: str) -> str:
    """Get emoji for a category"""
    emoji_map = {
        'technology': '🤖',
        'business': '💼',
        'science': '🔬',
        'politics': '🏛️',
        'entertainment': '🎬',
        'sports': '⚽',
        'health': '🏥',
        'environment': '🌍',
        'other': '📰'
    }
    
    return emoji_map.get(category.lower(), '📰') 