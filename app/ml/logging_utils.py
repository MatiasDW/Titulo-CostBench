"""
Structured logging utilities for the ML pipeline.
Uses structlog for JSON-formatted, contextual logging.
Falls back to standard logging with kwargs support.
"""
import logging
import sys
import json
from typing import Any

try:
    import structlog
    STRUCTLOG_AVAILABLE = True
except ImportError:
    STRUCTLOG_AVAILABLE = False


class KwargsLogger:
    """
    Wrapper around standard logging that accepts kwargs like structlog.
    Converts logger.info("event", key=value) to proper format.
    """
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(
                logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
            )
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)
    
    def _format_message(self, event: str, **kwargs) -> str:
        """Format message with event and kwargs."""
        if kwargs:
            extras = " ".join(f"{k}={v}" for k, v in kwargs.items())
            return f"{event} {extras}"
        return event
    
    def info(self, event: str, **kwargs):
        self.logger.info(self._format_message(event, **kwargs))
    
    def warning(self, event: str, **kwargs):
        self.logger.warning(self._format_message(event, **kwargs))
    
    def error(self, event: str, **kwargs):
        self.logger.error(self._format_message(event, **kwargs))
    
    def debug(self, event: str, **kwargs):
        self.logger.debug(self._format_message(event, **kwargs))


def get_logger(name: str = "ml_pipeline") -> Any:
    """
    Get a structured logger instance.
    
    Uses structlog if available, otherwise KwargsLogger wrapper.
    
    Args:
        name: Logger name (module identifier)
        
    Returns:
        Logger instance (structlog or KwargsLogger)
    """
    if STRUCTLOG_AVAILABLE:
        return structlog.get_logger(name)
    else:
        return KwargsLogger(name)


def configure_structlog():
    """Configure structlog with JSON output for production."""
    if not STRUCTLOG_AVAILABLE:
        return
    
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


# Pre-configured loggers for each module
def get_ingest_logger():
    return get_logger("ml.ingest")

def get_features_logger():
    return get_logger("ml.features")

def get_experiment_logger():
    return get_logger("ml.experiment")

def get_validation_logger():
    return get_logger("ml.validation")

def get_registry_logger():
    return get_logger("ml.registry")

