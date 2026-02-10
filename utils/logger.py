"""
Enhanced logging configuration
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional, Dict, List, Any
import json
from datetime import datetime

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON"""
        log_obj = {
            'timestamp': datetime.fromtimestamp(record.created).isoformat(),
            'level': record.levelname,
            'module': record.module,
            'function': record.funcName,
            'message': record.getMessage(),
            'thread': record.threadName,
            'process': record.processName
        }
        
        # Add exception info if present
        if record.exc_info:
            log_obj['exception'] = self.formatException(record.exc_info)
        
        # Add extra fields
        if hasattr(record, 'extra_fields'):
            log_obj.update(record.extra_fields)
        
        return json.dumps(log_obj, default=str)

class ColoredFormatter(logging.Formatter):
    """Colored console formatter"""
    
    COLORS = {
        'DEBUG': '\033[36m',      # Cyan
        'INFO': '\033[32m',       # Green
        'WARNING': '\033[33m',    # Yellow
        'ERROR': '\033[31m',      # Red
        'CRITICAL': '\033[41m'    # Red background
    }
    RESET = '\033[0m'
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record with colors"""
        levelname = record.levelname
        message = super().format(record)
        
        if levelname in self.COLORS:
            message = f"{self.COLORS[levelname]}{message}{self.RESET}"
        
        return message

def setup_logger(
    name: str = "HistoryTableGenerator",
    level: str = "INFO",
    log_file: Optional[str] = None,
    max_size_mb: int = 10,
    backup_count: int = 5,
    json_format: bool = False
) -> logging.Logger:
    """
    Setup application logger
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Path to log file
        max_size_mb: Maximum log file size in MB
        backup_count: Number of backup files to keep
        json_format: Whether to use JSON format
        
    Returns:
        logging.Logger: Configured logger
    """
    logger = logging.getLogger(name)
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Set level
    logger.setLevel(getattr(logging, level.upper()))
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    if json_format:
        console_formatter = JSONFormatter()
    else:
        console_formatter = ColoredFormatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file:
        # Create log directory if it doesn't exist
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_size_mb * 1024 * 1024,
            backupCount=backup_count,
            encoding='utf-8'
        )
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(module)s:%(funcName)s:%(lineno)d - %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger

def get_logger(name: str = "HistoryTableGenerator") -> logging.Logger:
    """
    Get or create logger instance
    
    Args:
        name: Logger name
        
    Returns:
        logging.Logger: Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger has no handlers, setup default configuration
    if not logger.handlers:
        # Load configuration from environment or use defaults
        log_level = os.getenv('LOG_LEVEL', 'INFO')
        log_file = os.getenv('LOG_FILE', 'logs/history_generator.log')
        
        logger = setup_logger(
            name=name,
            level=log_level,
            log_file=log_file
        )
    
    return logger

def log_with_context(
    logger: logging.Logger,
    level: str,
    message: str,
    **extra_fields
):
    """
    Log message with additional context fields
    
    Args:
        logger: Logger instance
        level: Log level
        message: Log message
        **extra_fields: Additional context fields
    """
    log_method = getattr(logger, level.lower())
    
    # Create log record with extra fields
    if extra_fields:
        # Create a new log record with extra attributes
        old_factory = logging.getLogRecordFactory()
        
        def record_factory(*args, **kwargs):
            record = old_factory(*args, **kwargs)
            record.extra_fields = extra_fields
            return record
        
        logging.setLogRecordFactory(record_factory)
        
        try:
            log_method(message)
        finally:
            # Restore original factory
            logging.setLogRecordFactory(old_factory)
    else:
        log_method(message)

class LogCapture:
    """Context manager for capturing logs"""
    
    def __init__(self, logger_name: str = "HistoryTableGenerator", level: str = "INFO"):
        self.logger_name = logger_name
        self.level = getattr(logging, level.upper())
        self.captured_records = []
        self.original_handlers = []
        
    def __enter__(self):
        """Enter context"""
        logger = logging.getLogger(self.logger_name)
        
        # Save original handlers
        self.original_handlers = logger.handlers.copy()
        
        # Clear existing handlers and add capturing handler
        logger.handlers.clear()
        
        capturing_handler = logging.Handler()
        capturing_handler.setLevel(self.level)
        capturing_handler.emit = self._capture_record
        logger.addHandler(capturing_handler)
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context"""
        logger = logging.getLogger(self.logger_name)
        
        # Remove capturing handler
        logger.handlers.clear()
        
        # Restore original handlers
        for handler in self.original_handlers:
            logger.addHandler(handler)
    
    def _capture_record(self, record: logging.LogRecord):
        """Capture log record"""
        self.captured_records.append(record)
    
    def get_messages(self) -> List[str]:
        """Get captured log messages"""
        return [record.getMessage() for record in self.captured_records]
    
    def get_records(self) -> List[logging.LogRecord]:
        """Get captured log records"""
        return self.captured_records.copy()