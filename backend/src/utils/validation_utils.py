"""
Validation Utilities

This module provides stateless validation functions that have no external
dependencies. These functions are safe to use throughout the application
for input validation and data sanitization.
"""

import re
import json
from typing import Any, Dict, List, Optional, Union
from .constants import EMAIL_PATTERN, UUID_PATTERN, PHONE_PATTERN


def validate_email(email: str) -> bool:
    """
    Validate email address format.
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    if not email or not isinstance(email, str):
        return False
    
    return bool(re.match(EMAIL_PATTERN, email.strip()))


def validate_uuid(uuid_string: str) -> bool:
    """
    Validate UUID format.
    
    Args:
        uuid_string: UUID string to validate
        
    Returns:
        True if UUID format is valid, False otherwise
    """
    if not uuid_string or not isinstance(uuid_string, str):
        return False
    
    return bool(re.match(UUID_PATTERN, uuid_string.strip().lower()))


def validate_phone(phone: str) -> bool:
    """
    Validate phone number format.
    
    Args:
        phone: Phone number to validate
        
    Returns:
        True if phone format is valid, False otherwise
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Remove common separators
    clean_phone = re.sub(r'[\s\-\(\)\.]+', '', phone)
    return bool(re.match(PHONE_PATTERN, clean_phone))


def validate_json_schema(data: Any, schema: Dict[str, Any]) -> tuple[bool, List[str]]:
    """
    Simple JSON schema validation.
    
    Args:
        data: Data to validate
        schema: Schema definition
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    def validate_field(value: Any, field_schema: Dict[str, Any], field_name: str = ""):
        field_errors = []
        
        # Check required fields
        if field_schema.get('required', False) and (value is None or value == ""):
            field_errors.append(f"{field_name} is required")
            return field_errors
        
        # Skip validation if value is None and not required
        if value is None:
            return field_errors
        
        # Type validation
        expected_type = field_schema.get('type')
        if expected_type:
            if expected_type == 'string' and not isinstance(value, str):
                field_errors.append(f"{field_name} must be a string")
            elif expected_type == 'integer' and not isinstance(value, int):
                field_errors.append(f"{field_name} must be an integer")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                field_errors.append(f"{field_name} must be a number")
            elif expected_type == 'boolean' and not isinstance(value, bool):
                field_errors.append(f"{field_name} must be a boolean")
            elif expected_type == 'array' and not isinstance(value, list):
                field_errors.append(f"{field_name} must be an array")
            elif expected_type == 'object' and not isinstance(value, dict):
                field_errors.append(f"{field_name} must be an object")
        
        # Length validation for strings
        if isinstance(value, str):
            min_length = field_schema.get('minLength')
            max_length = field_schema.get('maxLength')
            
            if min_length is not None and len(value) < min_length:
                field_errors.append(f"{field_name} must be at least {min_length} characters")
            
            if max_length is not None and len(value) > max_length:
                field_errors.append(f"{field_name} must be no more than {max_length} characters")
        
        # Range validation for numbers
        if isinstance(value, (int, float)):
            minimum = field_schema.get('minimum')
            maximum = field_schema.get('maximum')
            
            if minimum is not None and value < minimum:
                field_errors.append(f"{field_name} must be at least {minimum}")
            
            if maximum is not None and value > maximum:
                field_errors.append(f"{field_name} must be no more than {maximum}")
        
        # Pattern validation for strings
        pattern = field_schema.get('pattern')
        if pattern and isinstance(value, str):
            if not re.match(pattern, value):
                field_errors.append(f"{field_name} does not match required pattern")
        
        # Enum validation
        enum_values = field_schema.get('enum')
        if enum_values and value not in enum_values:
            field_errors.append(f"{field_name} must be one of: {', '.join(map(str, enum_values))}")
        
        return field_errors
    
    # Validate top-level object
    if not isinstance(data, dict):
        return False, ["Data must be an object"]
    
    # Validate each field in schema
    properties = schema.get('properties', {})
    for field_name, field_schema in properties.items():
        field_value = data.get(field_name)
        field_errors = validate_field(field_value, field_schema, field_name)
        errors.extend(field_errors)
    
    # Check for unexpected fields if additionalProperties is False
    if not schema.get('additionalProperties', True):
        for field_name in data.keys():
            if field_name not in properties:
                errors.append(f"Unexpected field: {field_name}")
    
    return len(errors) == 0, errors


def sanitize_input(value: Any, max_length: Optional[int] = None) -> str:
    """
    Sanitize input value for safe processing.
    
    Args:
        value: Input value to sanitize
        max_length: Maximum length to truncate to
        
    Returns:
        Sanitized string value
    """
    if value is None:
        return ""
    
    # Convert to string
    sanitized = str(value).strip()
    
    # Remove null bytes and control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Truncate if necessary
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized


def validate_url(url: str) -> bool:
    """
    Validate URL format.
    
    Args:
        url: URL to validate
        
    Returns:
        True if URL format is valid, False otherwise
    """
    if not url or not isinstance(url, str):
        return False
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return bool(url_pattern.match(url.strip()))


def validate_password_strength(password: str) -> tuple[bool, List[str]]:
    """
    Validate password strength.
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_strong, list_of_requirements_not_met)
    """
    if not password or not isinstance(password, str):
        return False, ["Password is required"]
    
    issues = []
    
    if len(password) < 8:
        issues.append("Password must be at least 8 characters long")
    
    if not re.search(r'[a-z]', password):
        issues.append("Password must contain at least one lowercase letter")
    
    if not re.search(r'[A-Z]', password):
        issues.append("Password must contain at least one uppercase letter")
    
    if not re.search(r'\d', password):
        issues.append("Password must contain at least one digit")
    
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        issues.append("Password must contain at least one special character")
    
    return len(issues) == 0, issues


def is_safe_filename(filename: str) -> bool:
    """
    Check if filename is safe for file system operations.
    
    Args:
        filename: Filename to validate
        
    Returns:
        True if filename is safe, False otherwise
    """
    if not filename or not isinstance(filename, str):
        return False
    
    # Check for dangerous patterns
    dangerous_patterns = [
        r'\.\./',  # Directory traversal
        r'^\.',    # Hidden files
        r'[<>:"|?*]',  # Invalid characters
        r'^(CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$',  # Windows reserved names
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, filename, re.IGNORECASE):
            return False
    
    # Check length
    if len(filename) > 255:
        return False
    
    return True


def validate_json_string(json_string: str) -> tuple[bool, Optional[Dict]]:
    """
    Validate and parse JSON string.
    
    Args:
        json_string: JSON string to validate
        
    Returns:
        Tuple of (is_valid, parsed_data_or_none)
    """
    if not json_string or not isinstance(json_string, str):
        return False, None
    
    try:
        parsed = json.loads(json_string.strip())
        return True, parsed
    except (json.JSONDecodeError, ValueError):
        return False, None 