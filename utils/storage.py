"""
Storage utilities for AI News Bot
Handles JSON file operations for data persistence
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from pathlib import Path

from config import config

logger = logging.getLogger(__name__)


def ensure_data_directories():
    """Ensure all necessary data directories exist"""
    data_dir = Path(config.data_dir)
    data_dir.mkdir(exist_ok=True)
    
    logger.info(f"Data directory ensured: {data_dir}")


def _get_data_file_path(filename: str) -> Path:
    """Get the full path to a data file"""
    data_dir = Path(config.data_dir)
    return data_dir / filename


def save_articles(articles: List[Dict[str, Any]]):
    """Save articles to JSON file"""
    try:
        file_path = _get_data_file_path('articles.json')
        
        data = {
            'articles': articles,
            'last_updated': datetime.now().isoformat(),
            'total_articles': len(articles)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(articles)} articles to {file_path}")
        
    except Exception as e:
        logger.error(f"Error saving articles: {e}")
        raise


def load_articles() -> Dict[str, Any]:
    """Load articles from JSON file"""
    try:
        file_path = _get_data_file_path('articles.json')
        
        if not file_path.exists():
            logger.info("Articles file not found, returning empty data")
            return {
                'articles': [],
                'last_updated': None,
                'total_articles': 0
            }
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Loaded {len(data.get('articles', []))} articles from {file_path}")
        return data
        
    except Exception as e:
        logger.error(f"Error loading articles: {e}")
        return {
            'articles': [],
            'last_updated': None,
            'total_articles': 0
        }


def save_summaries(summaries: Dict[str, Any]):
    """Save summaries to JSON file"""
    try:
        file_path = _get_data_file_path('summaries.json')
        
        data = {
            'summaries': summaries,
            'last_updated': datetime.now().isoformat(),
            'total_summaries': len(summaries)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved {len(summaries)} summaries to {file_path}")
        
    except Exception as e:
        logger.error(f"Error saving summaries: {e}")
        raise


def load_summaries() -> Dict[str, Any]:
    """Load summaries from JSON file"""
    try:
        file_path = _get_data_file_path('summaries.json')
        
        if not file_path.exists():
            logger.info("Summaries file not found, returning empty data")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        summaries = data.get('summaries', {})
        logger.info(f"Loaded {len(summaries)} summaries from {file_path}")
        return summaries
        
    except Exception as e:
        logger.error(f"Error loading summaries: {e}")
        return {}


def save_user_preferences(user_id: int, preferences: Dict[str, Any]):
    """Save user preferences to JSON file"""
    try:
        file_path = _get_data_file_path('users.json')
        
        # Load existing users
        users_data = load_all_users()
        
        # Update user preferences
        users_data[str(user_id)] = {
            **preferences,
            'last_updated': datetime.now().isoformat()
        }
        
        # Save updated data
        data = {
            'users': users_data,
            'last_updated': datetime.now().isoformat(),
            'total_users': len(users_data)
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved preferences for user {user_id}")
        
    except Exception as e:
        logger.error(f"Error saving user preferences: {e}")
        raise


def load_user_preferences(user_id: int) -> Dict[str, Any]:
    """Load user preferences from JSON file"""
    try:
        users_data = load_all_users()
        user_prefs = users_data.get(str(user_id), {})
        
        # Set default preferences if not exists
        if not user_prefs:
            user_prefs = {
                'preferred_category': 'technology',
                'max_articles': 5,
                'articles_read': 0,
                'articles_saved': 0,
                'saved_articles': [],
                'last_active': datetime.now().isoformat()
            }
        
        return user_prefs
        
    except Exception as e:
        logger.error(f"Error loading user preferences: {e}")
        return {
            'preferred_category': 'technology',
            'max_articles': 5,
            'articles_read': 0,
            'articles_saved': 0,
            'saved_articles': [],
            'last_active': datetime.now().isoformat()
        }


def load_all_users() -> Dict[str, Any]:
    """Load all users data from JSON file"""
    try:
        file_path = _get_data_file_path('users.json')
        
        if not file_path.exists():
            logger.info("Users file not found, returning empty data")
            return {}
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        users = data.get('users', {})
        logger.info(f"Loaded {len(users)} users from {file_path}")
        return users
        
    except Exception as e:
        logger.error(f"Error loading users: {e}")
        return {}


def update_user_activity(user_id: int):
    """Update user's last activity timestamp"""
    try:
        user_prefs = load_user_preferences(user_id)
        user_prefs['last_active'] = datetime.now().isoformat()
        save_user_preferences(user_id, user_prefs)
        
    except Exception as e:
        logger.error(f"Error updating user activity: {e}")


def increment_user_stat(user_id: int, stat_name: str, increment: int = 1):
    """Increment a user statistic"""
    try:
        user_prefs = load_user_preferences(user_id)
        current_value = user_prefs.get(stat_name, 0)
        user_prefs[stat_name] = current_value + increment
        save_user_preferences(user_id, user_prefs)
        
    except Exception as e:
        logger.error(f"Error incrementing user stat {stat_name}: {e}")


def get_user_stats(user_id: int) -> Dict[str, Any]:
    """Get comprehensive user statistics"""
    try:
        user_prefs = load_user_preferences(user_id)
        
        # Calculate additional stats
        saved_articles = user_prefs.get('saved_articles', [])
        articles_read = user_prefs.get('articles_read', 0)
        articles_saved = user_prefs.get('articles_saved', 0)
        
        return {
            'user_id': user_id,
            'preferred_category': user_prefs.get('preferred_category', 'technology'),
            'max_articles': user_prefs.get('max_articles', 5),
            'articles_read': articles_read,
            'articles_saved': articles_saved,
            'saved_articles_count': len(saved_articles),
            'last_active': user_prefs.get('last_active'),
            'created_at': user_prefs.get('created_at')
        }
        
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        return {}


def backup_data():
    """Create a backup of all data files"""
    try:
        data_dir = Path(config.data_dir)
        backup_dir = data_dir / 'backups'
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Backup each data file
        for filename in ['articles.json', 'summaries.json', 'users.json']:
            source_file = data_dir / filename
            if source_file.exists():
                backup_file = backup_dir / f"{filename}.{timestamp}"
                with open(source_file, 'r', encoding='utf-8') as src:
                    with open(backup_file, 'w', encoding='utf-8') as dst:
                        dst.write(src.read())
        
        logger.info(f"Data backup created at {backup_dir}")
        
    except Exception as e:
        logger.error(f"Error creating backup: {e}")


def cleanup_old_backups(max_backups: int = 10):
    """Clean up old backup files, keeping only the most recent ones"""
    try:
        data_dir = Path(config.data_dir)
        backup_dir = data_dir / 'backups'
        
        if not backup_dir.exists():
            return
        
        # Get all backup files
        backup_files = list(backup_dir.glob('*.json.*'))
        backup_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        
        # Remove old backups
        if len(backup_files) > max_backups:
            for old_backup in backup_files[max_backups:]:
                old_backup.unlink()
                logger.info(f"Removed old backup: {old_backup}")
        
    except Exception as e:
        logger.error(f"Error cleaning up backups: {e}") 