"""
Configuration Module

Handles application settings, environment variables, and system prompts.
"""

from config.settings import Settings
from config.prompts import ATITHI_SYSTEM_PROMPT

__all__ = [
    "Settings",
    "ATITHI_SYSTEM_PROMPT",
]
