"""
Application Constants

This module contains application-wide constants that are used across
multiple modules. These constants have no dependencies and are safe
to import from anywhere in the application.
"""

from enum import Enum
from typing import Dict, List

# Pagination defaults
DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# Text processing limits
MAX_TEXT_LENGTH = 10000
MAX_TITLE_LENGTH = 200
MAX_DESCRIPTION_LENGTH = 1000

# File handling
SUPPORTED_FILE_TYPES = [
    'txt', 'md', 'pdf', 'doc', 'docx', 
    'json', 'csv', 'xlsx', 'pptx'
]

MAX_FILE_SIZE_MB = 10
MAX_FILES_PER_UPLOAD = 5

# HTTP Status Codes (commonly used)
class HTTPStatus:
    """HTTP status codes for consistent usage across the application."""
    OK = 200
    CREATED = 201
    NO_CONTENT = 204
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CONFLICT = 409
    UNPROCESSABLE_ENTITY = 422
    INTERNAL_SERVER_ERROR = 500

HTTP_STATUS_CODES = HTTPStatus

# API Response formats
class ResponseFormat(Enum):
    """Standard response format types."""
    JSON = "json"
    XML = "xml"
    CSV = "csv"
    PDF = "pdf"

# Validation patterns
EMAIL_PATTERN = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
UUID_PATTERN = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
PHONE_PATTERN = r'^\+?1?\d{9,15}$'

# Date/Time formats
ISO_DATE_FORMAT = "%Y-%m-%d"
ISO_DATETIME_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
DISPLAY_DATE_FORMAT = "%B %d, %Y"
DISPLAY_DATETIME_FORMAT = "%B %d, %Y at %I:%M %p"

# Cache settings
DEFAULT_CACHE_TTL = 300  # 5 minutes
LONG_CACHE_TTL = 3600   # 1 hour
SHORT_CACHE_TTL = 60    # 1 minute

# Rate limiting
DEFAULT_RATE_LIMIT = 100  # requests per minute
BURST_RATE_LIMIT = 200   # burst allowance

# Logging levels
LOG_LEVELS = {
    'DEBUG': 10,
    'INFO': 20,
    'WARNING': 30,
    'ERROR': 40,
    'CRITICAL': 50
}

# Common error messages
ERROR_MESSAGES = {
    'INVALID_INPUT': 'Invalid input provided',
    'RESOURCE_NOT_FOUND': 'Requested resource not found',
    'UNAUTHORIZED_ACCESS': 'Unauthorized access attempt',
    'VALIDATION_FAILED': 'Input validation failed',
    'INTERNAL_ERROR': 'An internal error occurred',
    'RATE_LIMIT_EXCEEDED': 'Rate limit exceeded',
    'FILE_TOO_LARGE': f'File size exceeds {MAX_FILE_SIZE_MB}MB limit',
    'UNSUPPORTED_FILE_TYPE': f'File type not supported. Allowed: {", ".join(SUPPORTED_FILE_TYPES)}'
}

# Environment types
class Environment(Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production" 