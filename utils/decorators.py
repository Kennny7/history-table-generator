"""
Utility decorators for the application
"""

import functools
import time
from typing import Callable, Any, Optional
from datetime import datetime
from .logger import get_logger

def retry(max_attempts: int = 3, delay: float = 1.0, 
          backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """
    Retry decorator with exponential backoff
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt == max_attempts - 1:  # Last attempt
                        raise
                    
                    # Log retry attempt
                    logger = get_logger()
                    logger.warning(
                        f"Retry {attempt + 1}/{max_attempts} for {func.__name__}: "
                        f"{str(e)}. Waiting {current_delay} seconds..."
                    )
                    
                    time.sleep(current_delay)
                    current_delay *= backoff
            
            # This should never be reached
            raise last_exception
        return wrapper
    return decorator

def log_execution(log_args: bool = False, log_result: bool = False):
    """
    Log function execution details
    
    Args:
        log_args: Whether to log function arguments
        log_result: Whether to log function result
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_logger()
            
            # Log function call
            start_time = datetime.now()
            logger.debug(f"Executing {func.__module__}.{func.__name__}")
            
            if log_args:
                logger.debug(f"Arguments: args={args}, kwargs={kwargs}")
            
            try:
                result = func(*args, **kwargs)
                
                # Log result
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.debug(f"Completed {func.__name__} in {execution_time:.3f}s")
                
                if log_result and result is not None:
                    result_str = str(result)
                    if len(result_str) > 100:  # Truncate long results
                        result_str = result_str[:97] + "..."
                    logger.debug(f"Result: {result_str}")
                
                return result
            except Exception as e:
                execution_time = (datetime.now() - start_time).total_seconds()
                logger.error(
                    f"Failed {func.__name__} after {execution_time:.3f}s: "
                    f"{str(e)}"
                )
                raise
        return wrapper
    return decorator

def validate_input(validator_func: Optional[Callable] = None, 
                  error_message: str = "Invalid input"):
    """
    Validate function input using a validator function
    
    Args:
        validator_func: Function to validate input
        error_message: Error message if validation fails
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if validator_func:
                is_valid = validator_func(*args, **kwargs)
                if not is_valid:
                    raise ValueError(error_message)
            return func(*args, **kwargs)
        return wrapper
    return decorator

def transaction_aware(commit_on_success: bool = True):
    """
    Mark a function as transaction-aware
    
    Args:
        commit_on_success: Whether to commit on successful execution
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            # Check if object has transaction methods
            has_transaction = (
                hasattr(self, 'begin_transaction') and
                hasattr(self, 'commit_transaction') and
                hasattr(self, 'rollback_transaction')
            )
            
            if not has_transaction:
                return func(self, *args, **kwargs)
            
            # Begin transaction
            self.begin_transaction()
            
            try:
                result = func(self, *args, **kwargs)
                
                if commit_on_success:
                    self.commit_transaction()
                
                return result
            except Exception as e:
                self.rollback_transaction()
                raise
        return wrapper
    return decorator

def time_limit(timeout: float):
    """
    Set time limit for function execution
    
    Args:
        timeout: Maximum execution time in seconds
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import signal
            
            class TimeoutException(Exception):
                pass
            
            def timeout_handler(signum, frame):
                raise TimeoutException(f"Function {func.__name__} timed out after {timeout} seconds")
            
            # Set signal handler for timeout
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(int(timeout))
            
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                signal.alarm(0)  # Disable alarm
            
        return wrapper
    return decorator

def memoize(ttl: Optional[float] = None, maxsize: Optional[int] = 128):
    """
    Memoize decorator with TTL (time-to-live) support
    
    Args:
        ttl: Time-to-live in seconds (None for infinite)
        maxsize: Maximum cache size
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_info = {'hits': 0, 'misses': 0}
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key
            key = (args, frozenset(kwargs.items()))
            
            now = time.time()
            
            # Check cache
            if key in cache:
                value, timestamp = cache[key]
                
                # Check TTL
                if ttl is None or (now - timestamp) < ttl:
                    cache_info['hits'] += 1
                    return value
            
            # Cache miss or expired
            cache_info['misses'] += 1
            result = func(*args, **kwargs)
            
            # Clean cache if over maxsize
            if maxsize is not None and len(cache) >= maxsize:
                # Remove oldest entries
                sorted_items = sorted(cache.items(), key=lambda x: x[1][1])
                for old_key in [k for k, _ in sorted_items[:maxsize // 2]]:
                    del cache[old_key]
            
            # Store in cache
            cache[key] = (result, now)
            
            return result
        
        # Add cache info to wrapper
        wrapper.cache_info = lambda: cache_info.copy()
        wrapper.clear_cache = lambda: cache.clear()
        
        return wrapper
    return decorator