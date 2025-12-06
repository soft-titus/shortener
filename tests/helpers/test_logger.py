"""
Tests for the Logger helper (helpers/logger.py).
"""

import logging
import importlib
from unittest.mock import patch
import app.helpers.logger as logger_module


def test_logger_level():
    """Test that the shortener logger level matches the patched LOG_LEVEL."""


def reset_logging():
    """Reset Python logging configuration by removing all handlers and reloading logging."""
    root = logging.getLogger()
    for handler in root.handlers[:]:
        root.removeHandler(handler)
    logging.shutdown()
    importlib.reload(logging)

    with patch("app.helpers.logger.LOG_LEVEL", "DEBUG"):
        reset_logging()
        importlib.reload(logger_module)
        assert logger_module.logger.getEffectiveLevel() == logging.DEBUG

    with patch("app.helpers.logger.LOG_LEVEL", "WARNING"):
        reset_logging()
        importlib.reload(logger_module)
        assert logger_module.logger.getEffectiveLevel() == logging.WARNING
