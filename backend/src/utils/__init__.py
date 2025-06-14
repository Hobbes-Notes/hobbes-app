"""
Utils Package

This package contains stateless utility functions and helpers that have
NO upward dependencies. Utils should be dependency-free and reusable
across the entire application.

Organization:
- Pure utility functions (no external dependencies)
- Data transformation helpers
- Validation utilities
- Common constants and enums

IMPORTANT: Utils must not import from api, infrastructure, or any
application-specific modules to maintain clean architecture.
"""

from .text_utils import (
    sanitize_text,
    truncate_text,
    extract_keywords,
    normalize_whitespace
)

from .validation_utils import (
    validate_email,
    validate_uuid,
    validate_json_schema,
    sanitize_input
)

from .date_utils import (
    format_timestamp,
    parse_iso_date,
    get_utc_now,
    days_between
)

from .constants import (
    DEFAULT_PAGE_SIZE,
    MAX_TEXT_LENGTH,
    SUPPORTED_FILE_TYPES,
    HTTP_STATUS_CODES
)

__all__ = [
    # Text utilities
    'sanitize_text',
    'truncate_text',
    'extract_keywords',
    'normalize_whitespace',
    
    # Validation utilities
    'validate_email',
    'validate_uuid',
    'validate_json_schema',
    'sanitize_input',
    
    # Date utilities
    'format_timestamp',
    'parse_iso_date',
    'get_utc_now',
    'days_between',
    
    # Constants
    'DEFAULT_PAGE_SIZE',
    'MAX_TEXT_LENGTH',
    'SUPPORTED_FILE_TYPES',
    'HTTP_STATUS_CODES'
] 