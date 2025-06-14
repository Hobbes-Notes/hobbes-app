"""
Contract Tests for External APIs

These tests record and replay external API interactions to ensure
our integration contracts remain valid without hitting real APIs
during test runs.
"""

import pytest
import vcr
from unittest.mock import patch

from api.services.ai_service import AIService


@pytest.mark.vcr()
def test_ai_service_openai_contract():
    """
    Contract test for OpenAI API integration.
    
    This test records the actual API interaction on first run,
    then replays it on subsequent runs for fast, reliable testing.
    """
    # Use VCR to record/replay the API call
    with vcr.use_cassette('tests/fixtures/vcr_cassettes/openai_generate_response.yaml'):
        ai_service = AIService()
        
        # Test the actual API contract
        response = ai_service.generate_response(
            prompt="What is the capital of France?",
            max_tokens=50
        )
        
        # Verify the response structure matches our expectations
        assert isinstance(response, str)
        assert len(response) > 0
        assert "Paris" in response  # Expected content


@pytest.mark.vcr()
def test_ai_service_content_analysis_contract():
    """
    Contract test for AI content analysis.
    
    Records the API interaction for content analysis functionality.
    """
    with vcr.use_cassette('tests/fixtures/vcr_cassettes/openai_analyze_content.yaml'):
        ai_service = AIService()
        
        test_content = """
        This is a positive note about our project progress.
        We've made significant improvements in the user interface
        and the team is very motivated.
        """
        
        # Test content analysis contract
        analysis = ai_service.analyze_content(test_content)
        
        # Verify the analysis structure
        assert isinstance(analysis, dict)
        assert "sentiment" in analysis
        assert "topics" in analysis
        assert analysis["sentiment"] in ["positive", "negative", "neutral"]
        assert isinstance(analysis["topics"], list)


@pytest.mark.vcr()
def test_ai_service_error_handling_contract():
    """
    Contract test for AI service error handling.
    
    Tests how our service handles various API error conditions.
    """
    with vcr.use_cassette('tests/fixtures/vcr_cassettes/openai_error_handling.yaml'):
        ai_service = AIService()
        
        # Test with invalid/empty prompt
        with pytest.raises(ValueError):
            ai_service.generate_response("")
        
        # Test with excessive token request
        with pytest.raises(Exception):  # Should handle API rate limits gracefully
            ai_service.generate_response("test" * 10000, max_tokens=100000)


# Future: Add contract tests for other external services
@pytest.mark.skip(reason="Google OAuth not yet implemented")
@pytest.mark.vcr()
def test_google_oauth_contract():
    """
    Contract test for Google OAuth integration.
    
    This will test the OAuth flow when implemented.
    """
    pass


@pytest.mark.skip(reason="Database not yet implemented")
@pytest.mark.vcr()
def test_database_contract():
    """
    Contract test for database operations.
    
    This will test database schema and operations when implemented.
    """
    pass


# Helper function to clean up sensitive data from VCR cassettes
def scrub_sensitive_data(response):
    """
    Scrub sensitive data from VCR cassettes.
    
    This function removes API keys, tokens, and other sensitive
    information from recorded cassettes.
    """
    if 'authorization' in response['headers']:
        response['headers']['authorization'] = ['Bearer REDACTED']
    
    if 'x-api-key' in response['headers']:
        response['headers']['x-api-key'] = ['REDACTED']
    
    return response


# Configure VCR for all contract tests
@pytest.fixture(scope="module")
def vcr_config():
    """VCR configuration for contract tests."""
    return {
        "filter_headers": ["authorization", "x-api-key"],
        "before_record_response": scrub_sensitive_data,
        "ignore_localhost": True,
        "record_mode": "once",
        "match_on": ["uri", "method", "body"],
        "cassette_library_dir": "tests/fixtures/vcr_cassettes"
    } 