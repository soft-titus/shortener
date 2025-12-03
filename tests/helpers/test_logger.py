"""
Tests for the Logger helper (helpers/logger.py).
"""

import logging
import importlib
import app.helpers.logger as logger_module


def test_logger_level(monkeypatch):
    """Logger level matches the LOG_LEVEL environment variable."""

    def reset_logging():
        root = logging.getLogger()
        for handler in root.handlers[:]:
            root.removeHandler(handler)

    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    reset_logging()
    importlib.reload(logger_module)
    logger = logger_module.logger
    assert logger.getEffectiveLevel() == logging.DEBUG

    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    reset_logging()
    importlib.reload(logger_module)
    logger = logger_module.logger
    assert logger.getEffectiveLevel() == logging.WARNING
