import os
import pytest
from providers.gemini_provider import GeminiProvider
from providers.claude_provider import ClaudeProvider

@pytest.fixture
def test_data_dir():
    return os.path.join(os.path.dirname(__file__), 'test_data')

@pytest.fixture
def template_file(test_data_dir):
    return os.path.join(test_data_dir, 'test_limits.tex')

def test_gemini_provider_initialization():
    """Test that Gemini provider requires API key."""
    if 'GOOGLE_API_KEY' in os.environ:
        del os.environ['GOOGLE_API_KEY']
    
    with pytest.raises(ValueError) as exc_info:
        GeminiProvider()
    assert "GOOGLE_API_KEY environment variable must be set" in str(exc_info.value)

def test_claude_provider_initialization():
    """Test that Claude provider can be initialized."""
    provider = ClaudeProvider()
    assert provider is not None

def test_provider_output_format(template_file):
    """Test that provider outputs are properly formatted LaTeX."""
    # Only test if API key is available
    if 'GOOGLE_API_KEY' in os.environ:
        provider = GeminiProvider()
        response = provider.execute("Generate a simple limit problem in LaTeX.")
        assert response is not None
        assert "\\lim" in response
        assert "$" in response  # Should contain math delimiters

def test_provider_handles_files(template_file):
    """Test that providers can handle file inputs."""
    if 'GOOGLE_API_KEY' in os.environ:
        provider = GeminiProvider()
        response = provider.execute("Generate a similar problem.", [template_file])
        assert response is not None
        assert "\\lim" in response

def test_provider_error_handling():
    """Test that providers handle errors gracefully."""
    if 'GOOGLE_API_KEY' in os.environ:
        provider = GeminiProvider()
        with pytest.raises(Exception):
            # Try to read a non-existent file
            provider.execute("Generate something", ["nonexistent.tex"])
