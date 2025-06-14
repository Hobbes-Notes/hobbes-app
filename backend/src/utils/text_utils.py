"""
Text Utilities

This module provides stateless text processing utilities that have no
external dependencies. These functions are safe to use throughout the
application for common text operations.
"""

import re
import html
from typing import List, Optional, Set
from .constants import MAX_TEXT_LENGTH


def sanitize_text(text: str) -> str:
    """
    Sanitize text by removing potentially harmful content.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text safe for storage and display
    """
    if not text:
        return ""
    
    # HTML escape to prevent XSS
    sanitized = html.escape(text)
    
    # Remove null bytes and other control characters
    sanitized = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', sanitized)
    
    # Normalize whitespace
    sanitized = normalize_whitespace(sanitized)
    
    return sanitized


def truncate_text(text: str, max_length: int = MAX_TEXT_LENGTH, suffix: str = "...") -> str:
    """
    Truncate text to a maximum length with optional suffix.
    
    Args:
        text: Text to truncate
        max_length: Maximum allowed length
        suffix: Suffix to add when truncating
        
    Returns:
        Truncated text
    """
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    # Account for suffix length
    truncate_at = max_length - len(suffix)
    if truncate_at <= 0:
        return suffix[:max_length]
    
    # Try to truncate at word boundary
    truncated = text[:truncate_at]
    last_space = truncated.rfind(' ')
    
    if last_space > truncate_at * 0.8:  # If we can save 80% of the text
        truncated = truncated[:last_space]
    
    return truncated + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text by collapsing multiple spaces and trimming.
    
    Args:
        text: Text to normalize
        
    Returns:
        Text with normalized whitespace
    """
    if not text:
        return ""
    
    # Replace multiple whitespace characters with single space
    normalized = re.sub(r'\s+', ' ', text)
    
    # Trim leading and trailing whitespace
    return normalized.strip()


def extract_keywords(text: str, min_length: int = 3, max_keywords: int = 10) -> List[str]:
    """
    Extract keywords from text using simple heuristics.
    
    Args:
        text: Text to extract keywords from
        min_length: Minimum keyword length
        max_keywords: Maximum number of keywords to return
        
    Returns:
        List of extracted keywords
    """
    if not text:
        return []
    
    # Convert to lowercase and remove punctuation
    clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words
    words = clean_text.split()
    
    # Filter by length and remove common stop words
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have',
        'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should',
        'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we',
        'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
        'its', 'our', 'their'
    }
    
    keywords = []
    word_counts = {}
    
    for word in words:
        if (len(word) >= min_length and 
            word not in stop_words and 
            word.isalpha()):
            word_counts[word] = word_counts.get(word, 0) + 1
    
    # Sort by frequency and take top keywords
    sorted_words = sorted(word_counts.items(), key=lambda x: x[1], reverse=True)
    keywords = [word for word, count in sorted_words[:max_keywords]]
    
    return keywords


def count_words(text: str) -> int:
    """
    Count the number of words in text.
    
    Args:
        text: Text to count words in
        
    Returns:
        Number of words
    """
    if not text:
        return 0
    
    # Split on whitespace and filter empty strings
    words = [word for word in text.split() if word.strip()]
    return len(words)


def count_sentences(text: str) -> int:
    """
    Count the number of sentences in text.
    
    Args:
        text: Text to count sentences in
        
    Returns:
        Number of sentences
    """
    if not text:
        return 0
    
    # Simple sentence detection based on punctuation
    sentences = re.split(r'[.!?]+', text)
    # Filter out empty strings
    sentences = [s for s in sentences if s.strip()]
    return len(sentences)


def extract_emails(text: str) -> List[str]:
    """
    Extract email addresses from text.
    
    Args:
        text: Text to extract emails from
        
    Returns:
        List of email addresses found
    """
    if not text:
        return []
    
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    emails = re.findall(email_pattern, text)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_emails = []
    for email in emails:
        if email.lower() not in seen:
            seen.add(email.lower())
            unique_emails.append(email)
    
    return unique_emails


def slug_from_text(text: str, max_length: int = 50) -> str:
    """
    Create a URL-friendly slug from text.
    
    Args:
        text: Text to convert to slug
        max_length: Maximum slug length
        
    Returns:
        URL-friendly slug
    """
    if not text:
        return ""
    
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and special characters with hyphens
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[-\s]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Truncate if necessary
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug 