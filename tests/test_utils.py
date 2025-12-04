"""
Tests for app.utils.
"""

from app.utils import generate_short_code


def test_generate_short_code_length():
    """generate_short_code returns a string of correct length."""
    code = generate_short_code(12)
    assert isinstance(code, str)
    assert len(code) == 12
    assert code.isalnum()


def test_generate_short_code_default_length():
    """generate_code returns 8 chars by default."""
    code = generate_short_code()
    assert isinstance(code, str)
    assert len(code) == 8
    assert code.isalnum()
