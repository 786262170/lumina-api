"""
Logging configuration for the application
"""
import logging
import sys
from app.config import settings

# Create logger
logger = logging.getLogger("lumina_api")

# Set log level based on environment
if settings.debug:
    log_level = logging.DEBUG
else:
    log_level = logging.INFO

logger.setLevel(log_level)

# Create console handler if not exists
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(log_level)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    handler.setFormatter(formatter)
    
    # Add handler to logger
    logger.addHandler(handler)

# Prevent duplicate logs
logger.propagate = False

