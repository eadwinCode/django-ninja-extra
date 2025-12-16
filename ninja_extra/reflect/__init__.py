"""
Ellar Reflect: A module for managing metadata on callables and types.
Provides tools to attach, retrieve, and manage metadata for dependency injection and other framework features.
"""

from ._reflect import reflect
from .utils import ensure_target, fail_silently, transfer_metadata

__all__ = ["reflect", "ensure_target", "transfer_metadata", "fail_silently"]
