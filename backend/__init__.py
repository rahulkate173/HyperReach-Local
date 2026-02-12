"""
Cold Outreach Engine - Backend Package
"""

__version__ = "1.0.0"
__author__ = "Outreach Engine Team"

from backend.config import settings
from backend.api import app

__all__ = ["settings", "app"]
