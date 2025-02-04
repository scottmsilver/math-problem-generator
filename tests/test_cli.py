import os
import pytest
import tempfile
from generate_problems import setup_args

@pytest.fixture
def test_data_dir():
    return os.path.join(os.path.dirname(__file__), 'test_data')

@pytest.fixture
def template_file(test_data_dir):
    return os.path.join(test_data_dir, 'test_limits.tex')

def test_cli_args_basic(template_file):
    """Test basic command line argument parsing."""
    parser = setup_args()
    args = parser.parse_args([template_file])
    assert args.template_file == template_file
    assert args.provider == 'claude'  # default
    assert args.difficulty == 'same'  # default
    assert args.num_problems == 5  # default

def test_cli_args_full(template_file):
    """Test parsing all command line arguments."""
    parser = setup_args()
    args = parser.parse_args([
        template_file,
        '--output-dir', 'output',
        '--provider', 'gemini',
        '--difficulty', 'challenge',
        '--num-problems', '3'
    ])
    assert args.template_file == template_file
    assert args.output_dir == 'output'
    assert args.provider == 'gemini'
    assert args.difficulty == 'challenge'
    assert args.num_problems == 3

def test_cli_args_validation(template_file):
    """Test validation of command line arguments."""
    parser = setup_args()
    
    # Test invalid provider
    with pytest.raises(SystemExit):
        parser.parse_args([template_file, '--provider', 'invalid'])
    
    # Test invalid difficulty
    with pytest.raises(SystemExit):
        parser.parse_args([template_file, '--difficulty', 'invalid'])
    
    # Test invalid number of problems
    with pytest.raises(SystemExit):
        parser.parse_args([template_file, '--num-problems', 'invalid'])
