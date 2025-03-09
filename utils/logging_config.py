#!/usr/bin/env python3
import os
import logging
import logging.handlers
from datetime import datetime

def setup_logging(log_level=logging.INFO, log_to_file=True, log_dir=None):
    """
    Setup logging configuration
    
    Args:
        log_level (int): Logging level (default: INFO)
        log_to_file (bool): Whether to log to file (default: True)
        log_dir (str): Directory to store log files (default: logs in current directory)
        
    Returns:
        logging.Logger: Configured logger
    """
    # Create root logger
    logger = logging.getLogger("SAST_Agent")
    logger.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # Add console handler to logger
    logger.addHandler(console_handler)
    
    # Add file handler if requested
    if log_to_file:
        if not log_dir:
            log_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs")
        
        # Create log directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        # Create log file with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = os.path.join(log_dir, f"sast_agent_{timestamp}.log")
        
        # Create file handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        
        # Add file handler to logger
        logger.addHandler(file_handler)
        
        logger.info(f"Logging to file: {log_file}")
    
    return logger

def get_logger(name=None):
    """
    Get a logger with the given name
    
    Args:
        name (str): Logger name (default: None for root logger)
        
    Returns:
        logging.Logger: Logger instance
    """
    if name:
        return logging.getLogger(f"SAST_Agent.{name}")
    return logging.getLogger("SAST_Agent")
