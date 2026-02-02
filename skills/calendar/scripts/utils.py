#!/usr/bin/env python3
"""
Shared utilities for ChatGPT Skills modules

This module provides common functionality used across all skill modules:
- API key loading from environment and .env files
- Logging configuration
- Common helper functions
"""

import os
import logging
from pathlib import Path
from typing import Optional, List

# Configure logging
def setup_logging(name: str, level: int = logging.INFO) -> logging.Logger:
    """
    Set up logging for a module

    Args:
        name: Logger name (usually __name__)
        level: Logging level (default INFO)

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Only add handler if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


def load_env_file(env_paths: Optional[List[Path]] = None) -> None:
    """
    Load environment variables from .env files

    Args:
        env_paths: List of paths to check for .env files
                  If None, uses default paths
    """
    if env_paths is None:
        env_paths = [
            Path.home() / ".env",
            Path.home() / ".claude" / ".env",
            Path.cwd() / ".env",
        ]

    for env_path in env_paths:
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")
                            if key not in os.environ:
                                os.environ[key] = value
            except (IOError, UnicodeDecodeError) as e:
                # Silently continue to next file
                continue
            break


def get_api_key(key_name: str, env_paths: Optional[List[Path]] = None) -> Optional[str]:
    """
    Get API key from environment or .env files

    Args:
        key_name: Environment variable name (e.g., 'OPENAI_API_KEY')
        env_paths: Optional list of .env file paths to check

    Returns:
        API key string or None if not found
    """
    # First try environment variable
    api_key = os.environ.get(key_name)
    if api_key:
        return api_key

    # Load from .env files
    load_env_file(env_paths)

    return os.environ.get(key_name)


def get_openai_api_key() -> Optional[str]:
    """Get OpenAI API key"""
    return get_api_key('OPENAI_API_KEY')


def get_kie_api_key() -> Optional[str]:
    """Get KIE.AI API key"""
    # Try multiple possible key names
    key = get_api_key('KIE_API_KEY')
    if not key:
        key = get_api_key('SORA_API_KEY')
    return key


def sanitize_error_message(error: Exception) -> str:
    """
    Sanitize error message to avoid exposing sensitive data

    Args:
        error: Exception instance

    Returns:
        Safe error message string
    """
    message = str(error)

    # List of patterns that might contain sensitive data
    sensitive_patterns = [
        'sk-',      # OpenAI API keys
        'key=',     # Generic API keys in URLs
        'token=',   # Tokens in URLs
        'password', # Passwords
        'secret',   # Secrets
    ]

    for pattern in sensitive_patterns:
        if pattern.lower() in message.lower():
            return f"Error occurred (details hidden for security)"

    return message


def validate_file_path(path: str, allowed_extensions: Optional[List[str]] = None) -> bool:
    """
    Validate file path to prevent path traversal attacks

    Args:
        path: File path to validate
        allowed_extensions: Optional list of allowed file extensions

    Returns:
        True if path is valid, False otherwise
    """
    try:
        # Resolve to absolute path
        resolved = Path(path).resolve()

        # Check for path traversal
        if '..' in str(path):
            return False

        # Check extension if specified
        if allowed_extensions:
            ext = resolved.suffix.lower()
            if ext not in [e.lower() for e in allowed_extensions]:
                return False

        return True
    except (ValueError, OSError):
        return False


def validate_url(url: str) -> bool:
    """
    Basic URL validation

    Args:
        url: URL string to validate

    Returns:
        True if URL appears valid, False otherwise
    """
    if not url:
        return False

    # Must start with http:// or https://
    if not url.startswith(('http://', 'https://')):
        return False

    # Basic length check
    if len(url) > 2048:
        return False

    return True


def truncate_string(s: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate string to maximum length

    Args:
        s: String to truncate
        max_length: Maximum length
        suffix: Suffix to add if truncated

    Returns:
        Truncated string
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


# Version info
__version__ = "1.0.0"
__author__ = "ChatGPT Skills"
