"""
Utility functions for the application.
"""

import string
import random


def generate_short_code(length: int = 8) -> str:
    """
    Generate a random alphanumeric short code.

    Args:
        length (int): Length of the short code.

    Returns:
        str: Random short code.
    """
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choices(alphabet, k=length))
