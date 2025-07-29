"""
Simple Task Scheduler for AI News Bot
Handles background tasks without Celery
"""

import asyncio
import logging
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Callable, Optional
import time

from config import config
from .news_tasks import NewsTasks

logger = logging.getLogger(__name__)


class TaskScheduler:
    """Simple task scheduler for background tasks"""
    
    def __init__(self):
        self.running = False
        self.tasks = {}
        self.news_tasks = NewsTasks()
        self.scheduler_thread = None
    
    def start(self):
        """Start the task scheduler"""
        if self.running:
            logger.warning("Task scheduler is already running")
            return
        
        self.running = True
        logger.info("Starting task scheduler...")
        
        # Start scheduler in a separate thread
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        # Schedule initial tasks
        self._schedule_initial_tasks()
    
    def stop(self):
        """Stop the task scheduler"""
        if not self.running:
            return
        
        logger.info("Stopping task scheduler...")
        self.running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
    
    def _run_scheduler(self):
        """Main scheduler loop"""
        while self.running:
            try:
                current_time = datetime.now()
                
                # Check for tasks that need to be executed
                tasks_to_run = []
                for task_id, task_info in self.tasks.items():
                    if task_info['next_run'] <= current_time:
                        tasks_to_run.append((task_id, task_info))
                
                # Execute tasks
                for task_id, task_info in tasks_to_run:
                    self._execute_task(task_id, task_info)
                
                # Sleep for a short interval
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Error in scheduler loop: {e}")
                time.sleep(60)  # Continue after error
    
    def _schedule_initial_tasks(self):
        """Schedule initial background tasks"""
        # Schedule news scraping task
        self.schedule_recurring_task(
            'news_scraping',
            self.news_tasks.scrape_and_process_news,
            interval_minutes=config.scrape_interval_minutes
        )
        
        # Schedule cleanup task (daily)
        self.schedule_recurring_task(
            'cleanup',
            self.news_tasks.cleanup_old_data,
            interval_minutes=1440  # 24 hours
        )
        
        logger.info("Initial tasks scheduled")
    
    def schedule_recurring_task(self, task_id: str, task_func: Callable, interval_minutes: int):
        """Schedule a recurring task"""
        next_run = datetime.now() + timedelta(minutes=interval_minutes)
        
        self.tasks[task_id] = {
            'func': task_func,
            'interval_minutes': interval_minutes,
            'next_run': next_run,
            'last_run': None,
            'run_count': 0
        }
        
        logger.info(f"Scheduled task '{task_id}' to run every {interval_minutes} minutes")
    
    def schedule_one_time_task(self, task_id: str, task_func: Callable, delay_minutes: int):
        """Schedule a one-time task"""
        next_run = datetime.now() + timedelta(minutes=delay_minutes)
        
        self.tasks[task_id] = {
            'func': task_func,
            'interval_minutes': None,  # One-time task
            'next_run': next_run,
            'last_run': None,
            'run_count': 0
        }
        
        logger.info(f"Scheduled one-time task '{task_id}' to run in {delay_minutes} minutes")
    
    def _execute_task(self, task_id: str, task_info: Dict[str, Any]):
        """Execute a scheduled task"""
        try:
            logger.info(f"Executing task: {task_id}")
            
            # Update task info
            task_info['last_run'] = datetime.now()
            task_info['run_count'] += 1
            
            # Execute the task
            if asyncio.iscoroutinefunction(task_info['func']):
                # Create new event loop for async task
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(task_info['func']())
                finally:
                    loop.close()
            else:
                # Execute sync task
                task_info['func']()
            
            # Schedule next run for recurring tasks
            if task_info['interval_minutes']:
                task_info['next_run'] = datetime.now() + timedelta(minutes=task_info['interval_minutes'])
                logger.info(f"Task '{task_id}' completed, next run scheduled for {task_info['next_run']}")
            else:
                # Remove one-time task
                del self.tasks[task_id]
                logger.info(f"One-time task '{task_id}' completed and removed")
            
        except Exception as e:
            logger.error(f"Error executing task '{task_id}': {e}")
            
            # Reschedule recurring task even if it failed
            if task_info['interval_minutes']:
                task_info['next_run'] = datetime.now() + timedelta(minutes=task_info['interval_minutes'])
                logger.info(f"Task '{task_id}' failed, rescheduled for {task_info['next_run']}")
    
    def get_task_status(self) -> Dict[str, Any]:
        """Get status of all scheduled tasks"""
        status = {}
        for task_id, task_info in self.tasks.items():
            status[task_id] = {
                'next_run': task_info['next_run'].isoformat(),
                'last_run': task_info['last_run'].isoformat() if task_info['last_run'] else None,
                'run_count': task_info['run_count'],
                'interval_minutes': task_info['interval_minutes']
            }
        return status
    
    def cancel_task(self, task_id: str) -> bool:
        """Cancel a scheduled task"""
        if task_id in self.tasks:
            del self.tasks[task_id]
            logger.info(f"Task '{task_id}' cancelled")
            return True
        return False
    
    def is_running(self) -> bool:
        """Check if scheduler is running"""
        return self.running 