# app/services/stats_cache.py (Optional)

from functools import wraps
from datetime import datetime, timedelta
import json

# Simple in-memory cache (for production, use Redis)
_cache = {}
_cache_timeout = {}

def cached_stats(timeout_minutes=5):
    """
    Decorator to cache statistics results.
    
    Args:
        timeout_minutes (int): Cache timeout in minutes
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{func.__name__}:{json.dumps(args)}:{json.dumps(kwargs)}"
            now = datetime.now()
            
            # Check if cached and not expired
            if cache_key in _cache:
                if cache_key in _cache_timeout:
                    if now < _cache_timeout[cache_key]:
                        return _cache[cache_key]
            
            # Calculate new result
            result = func(*args, **kwargs)
            
            # Store in cache
            _cache[cache_key] = result
            _cache_timeout[cache_key] = now + timedelta(minutes=timeout_minutes)
            
            return result
        return wrapper
    return decorator

# Usage example:
# @cached_stats(timeout_minutes=10)
# def get_expensive_stats():
#     return StatsService.get_dashboard_stats()