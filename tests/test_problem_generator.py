import os
import pytest
import tempfile
from utils.problem_generator import ProblemGenerator
from tests.mock_provider import MockProvider

@pytest.fixture
def test_data_dir():
    return os.path.join(os.path.dirname(__file__), 'test_data')

@pytest.fixture
def template_file(test_data_dir):
    return os.path.join(test_data_dir, 'test_limits.tex')

@pytest.fixture
def mock_provider():
    return MockProvider()

@pytest.fixture
def problem_generator(mock_provider):
    return ProblemGenerator(mock_provider)

def test_generate_problems_basic(problem_generator, template_file):
    """Test basic problem generation with default settings."""
    problems = problem_generator.generate_problems(template_file)
    assert problems is not None
    assert "\\begin{enumerate}" in problems
    assert "\\end{enumerate}" in problems
    assert "$\\displaystyle \\lim" in problems

def test_generate_problems_with_num(problem_generator, template_file):
    """Test generating a specific number of problems."""
    num_problems = 3
    problems = problem_generator.generate_problems(template_file, num_problems=num_problems)
    # Count \item occurrences to verify number of problems
    assert problems.count("\\item") == num_problems

def test_generate_problems_difficulty(problem_generator, template_file):
    """Test generating problems with different difficulty levels."""
    # Test 'challenge' mode (20% challenging)
    problems = problem_generator.generate_problems(template_file, difficulty='challenge', num_problems=5)
    assert "[Challenge]" in problems
    
    # Test 'harder' mode (80% challenging)
    problems = problem_generator.generate_problems(template_file, difficulty='harder', num_problems=5)
    assert "[Challenge]" in problems

def test_generate_solutions(problem_generator, template_file):
    """Test solution generation."""
    problems = problem_generator.generate_problems(template_file)
    solutions = problem_generator.generate_solutions(problems)
    assert solutions is not None
    assert "Solution:" in solutions
    assert "\\begin{align*}" in solutions
    assert "\\end{align*}" in solutions

def test_create_problem_set(problem_generator, template_file):
    """Test creating a complete problem set with output files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        problems_pdf, solutions_pdf = problem_generator.create_problem_set(
            template_file,
            output_dir=temp_dir,
            difficulty='challenge',
            num_problems=3
        )
        
        # Check that files were created
        assert os.path.exists(problems_pdf)
        assert os.path.exists(solutions_pdf)
        assert os.path.exists(os.path.join(temp_dir, 'problems.tex'))
        assert os.path.exists(os.path.join(temp_dir, 'solutions.tex'))

def test_prompt_content(problem_generator, template_file):
    """Test that prompts contain expected content."""
    problem_generator.generate_problems(template_file, difficulty='challenge', num_problems=5)
    prompt = problem_generator.provider.last_prompt
    
    # Check prompt contains key instructions
    assert "Generate 5 LaTeX math problems" in prompt
    assert "more challenging than the example" in prompt
    assert "\\textbf{[Challenge]}" in prompt
