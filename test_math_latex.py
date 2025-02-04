import os
import pytest
import tempfile
from math_latex import MathLatexConverter
from providers.claude_provider import ClaudeProvider

@pytest.fixture
def log_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir

@pytest.fixture
def converter(log_dir):
    provider = ClaudeProvider()
    return MathLatexConverter(provider, log_dir)

def test_pdf_conversion(converter):
    # Use the existing limits.pdf
    pdf_path = 'limits.pdf'
    assert os.path.exists(pdf_path), "Test PDF file not found"
    
    # Convert to LaTeX
    latex = converter.convert_to_latex(pdf_path)
    assert latex is not None
    assert len(latex) > 0
    
    # Validate the conversion
    assert converter.validate_conversion(pdf_path, latex)

def test_image_conversion(converter):
    # Use the existing test_pattern.png
    image_path = 'test_pattern.png'
    assert os.path.exists(image_path), "Test image file not found"
    
    # Convert to LaTeX
    latex = converter.convert_to_latex(image_path)
    assert latex is not None
    assert len(latex) > 0
    
    # Validate the conversion
    assert converter.validate_conversion(image_path, latex)
