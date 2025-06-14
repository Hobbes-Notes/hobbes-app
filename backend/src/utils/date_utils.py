"""
Date Utilities

This module provides stateless date and time utilities that have no external
dependencies. These functions are safe to use throughout the application
for common date/time operations.
"""

from datetime import datetime, timezone, timedelta
from typing import Optional, Union
from .constants import ISO_DATE_FORMAT, ISO_DATETIME_FORMAT, DISPLAY_DATE_FORMAT, DISPLAY_DATETIME_FORMAT


def get_utc_now() -> datetime:
    """
    Get current UTC datetime.
    
    Returns:
        Current UTC datetime
    """
    return datetime.now(timezone.utc)


def format_timestamp(dt: datetime, format_string: str = ISO_DATETIME_FORMAT) -> str:
    """
    Format datetime to string.
    
    Args:
        dt: Datetime to format
        format_string: Format string to use
        
    Returns:
        Formatted datetime string
    """
    if not dt:
        return ""
    
    # Ensure timezone awareness
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    return dt.strftime(format_string)


def parse_iso_date(date_string: str) -> Optional[datetime]:
    """
    Parse ISO format date string to datetime.
    
    Args:
        date_string: ISO format date string
        
    Returns:
        Parsed datetime or None if invalid
    """
    if not date_string or not isinstance(date_string, str):
        return None
    
    # Try different ISO formats
    formats_to_try = [
        "%Y-%m-%dT%H:%M:%S.%fZ",      # 2023-01-01T12:00:00.000Z
        "%Y-%m-%dT%H:%M:%SZ",         # 2023-01-01T12:00:00Z
        "%Y-%m-%dT%H:%M:%S.%f",       # 2023-01-01T12:00:00.000
        "%Y-%m-%dT%H:%M:%S",          # 2023-01-01T12:00:00
        "%Y-%m-%d %H:%M:%S",          # 2023-01-01 12:00:00
        "%Y-%m-%d",                   # 2023-01-01
    ]
    
    for fmt in formats_to_try:
        try:
            dt = datetime.strptime(date_string.strip(), fmt)
            # Add UTC timezone if not present
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    
    return None


def days_between(start_date: datetime, end_date: datetime) -> int:
    """
    Calculate number of days between two dates.
    
    Args:
        start_date: Start date
        end_date: End date
        
    Returns:
        Number of days between dates (can be negative)
    """
    if not start_date or not end_date:
        return 0
    
    # Convert to date objects for day calculation
    start = start_date.date() if hasattr(start_date, 'date') else start_date
    end = end_date.date() if hasattr(end_date, 'date') else end_date
    
    return (end - start).days


def add_days(dt: datetime, days: int) -> datetime:
    """
    Add days to a datetime.
    
    Args:
        dt: Base datetime
        days: Number of days to add (can be negative)
        
    Returns:
        New datetime with days added
    """
    if not dt:
        return get_utc_now()
    
    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """
    Add hours to a datetime.
    
    Args:
        dt: Base datetime
        hours: Number of hours to add (can be negative)
        
    Returns:
        New datetime with hours added
    """
    if not dt:
        return get_utc_now()
    
    return dt + timedelta(hours=hours)


def start_of_day(dt: datetime) -> datetime:
    """
    Get start of day (00:00:00) for given datetime.
    
    Args:
        dt: Input datetime
        
    Returns:
        Datetime at start of day
    """
    if not dt:
        dt = get_utc_now()
    
    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: datetime) -> datetime:
    """
    Get end of day (23:59:59.999999) for given datetime.
    
    Args:
        dt: Input datetime
        
    Returns:
        Datetime at end of day
    """
    if not dt:
        dt = get_utc_now()
    
    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def is_weekend(dt: datetime) -> bool:
    """
    Check if datetime falls on a weekend.
    
    Args:
        dt: Datetime to check
        
    Returns:
        True if weekend (Saturday or Sunday), False otherwise
    """
    if not dt:
        return False
    
    # weekday() returns 0-6 where Monday is 0 and Sunday is 6
    return dt.weekday() >= 5


def format_relative_time(dt: datetime, reference: Optional[datetime] = None) -> str:
    """
    Format datetime as relative time (e.g., "2 hours ago", "in 3 days").
    
    Args:
        dt: Datetime to format
        reference: Reference datetime (defaults to now)
        
    Returns:
        Relative time string
    """
    if not dt:
        return "unknown"
    
    if reference is None:
        reference = get_utc_now()
    
    # Ensure both datetimes are timezone-aware
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if reference.tzinfo is None:
        reference = reference.replace(tzinfo=timezone.utc)
    
    delta = reference - dt
    total_seconds = delta.total_seconds()
    
    # Future times
    if total_seconds < 0:
        total_seconds = abs(total_seconds)
        prefix = "in "
        suffix = ""
    else:
        prefix = ""
        suffix = " ago"
    
    # Calculate time units
    if total_seconds < 60:
        return f"{prefix}just now" if total_seconds < 10 else f"{prefix}{int(total_seconds)} seconds{suffix}"
    elif total_seconds < 3600:
        minutes = int(total_seconds // 60)
        return f"{prefix}{minutes} minute{'s' if minutes != 1 else ''}{suffix}"
    elif total_seconds < 86400:
        hours = int(total_seconds // 3600)
        return f"{prefix}{hours} hour{'s' if hours != 1 else ''}{suffix}"
    elif total_seconds < 2592000:  # 30 days
        days = int(total_seconds // 86400)
        return f"{prefix}{days} day{'s' if days != 1 else ''}{suffix}"
    elif total_seconds < 31536000:  # 365 days
        months = int(total_seconds // 2592000)
        return f"{prefix}{months} month{'s' if months != 1 else ''}{suffix}"
    else:
        years = int(total_seconds // 31536000)
        return f"{prefix}{years} year{'s' if years != 1 else ''}{suffix}"


def get_age_in_years(birth_date: datetime, reference_date: Optional[datetime] = None) -> int:
    """
    Calculate age in years from birth date.
    
    Args:
        birth_date: Birth date
        reference_date: Reference date (defaults to now)
        
    Returns:
        Age in years
    """
    if not birth_date:
        return 0
    
    if reference_date is None:
        reference_date = get_utc_now()
    
    age = reference_date.year - birth_date.year
    
    # Adjust if birthday hasn't occurred this year
    if (reference_date.month, reference_date.day) < (birth_date.month, birth_date.day):
        age -= 1
    
    return max(0, age)


def is_business_day(dt: datetime) -> bool:
    """
    Check if datetime falls on a business day (Monday-Friday).
    
    Args:
        dt: Datetime to check
        
    Returns:
        True if business day, False otherwise
    """
    if not dt:
        return False
    
    # weekday() returns 0-6 where Monday is 0 and Sunday is 6
    return dt.weekday() < 5


def next_business_day(dt: datetime) -> datetime:
    """
    Get the next business day after given datetime.
    
    Args:
        dt: Input datetime
        
    Returns:
        Next business day datetime
    """
    if not dt:
        dt = get_utc_now()
    
    next_day = dt + timedelta(days=1)
    
    # Skip weekends
    while not is_business_day(next_day):
        next_day += timedelta(days=1)
    
    return next_day 