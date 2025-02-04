import os
import pytest
import tempfile

@pytest.fixture(scope='session')
def test_data_dir():
    """Path to test data directory."""
    return os.path.join(os.path.dirname(__file__), 'test_data')

@pytest.fixture(scope='session')
def template_file(test_data_dir):
    """Path to test template file."""
    return os.path.join(test_data_dir, 'test_limits.tex')

@pytest.fixture
def temp_output_dir():
    """Temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir
