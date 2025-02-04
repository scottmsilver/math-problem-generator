import os
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import tempfile
from .latex_compiler import LatexCompiler
from providers.claude_provider import ClaudeProvider

class ProblemGenerator:
    def __init__(self, provider=None):
        """Initialize the problem generator with an LLM provider."""
        self.provider = provider or ClaudeProvider()
        self.latex_compiler = LatexCompiler()
        
    def generate_problems(self, template_file: str, difficulty: str = 'same', num_problems: int = 5) -> str:
        """Generate problems based on the template and difficulty level."""
        with open(template_file, 'r') as f:
            template_content = f.read()
            
        # Calculate number of challenging problems based on difficulty
        num_challenging = {
            'same': 0,
            'challenge': int(num_problems * 0.2),  # 20% challenging
            'harder': int(num_problems * 0.8)  # 80% challenging
        }.get(difficulty, 0)
        
        # Create prompt based on difficulty
        prompt = f"""Generate {num_problems} LaTeX math problems about limits, following these rules:
1. Use similar notation and style as the example.
2. Include a mix of different types of limits (polynomials, rational functions, exponential).
3. {num_challenging} problems should be more challenging than the example.
4. Mark challenging problems with \\textbf{{[Challenge]}} before the problem.
5. Use \\begin{{enumerate}} to list the problems.
6. Use \\displaystyle for all limits.
7. Return ONLY the LaTeX code for the problems, without any document class or preamble.

Example problems:
{template_content}"""

        # Get problems from LLM
        problems = self.provider.execute(prompt)
        
        # Ensure problems are wrapped in enumerate
        if "\\begin{enumerate}" not in problems:
            problems = "\\begin{enumerate}\n" + problems + "\n\\end{enumerate}"
            
        return problems
        
    def generate_solutions(self, problems_latex: str) -> str:
        """Generate solutions for the given problems."""
        prompt = f"""Generate detailed solutions for these math problems. Follow these rules:
1. Each solution should:
   - Start with "Solution:" on its own line
   - Show the original problem
   - Use align* environment for step-by-step solutions
   - Include explanatory text for key steps
   - Box the final answer using \\boxed{{}}
2. For problems marked as [Challenge], provide extra detail in the explanations.
3. Use proper LaTeX notation (e.g., \\displaystyle for limits).
4. Return ONLY the LaTeX code for the solutions.

Problems to solve:
{problems_latex}"""

        # Get solutions from LLM
        solutions = self.provider.execute(prompt)
        
        # Add custom spacing commands for better formatting
        preamble = """% Custom spacing for limit notation
\\def\\limit#1{\\lim\\limits_{#1}\\;}
\\def\\infinity{\\infty}

% Better fraction spacing
\\setlength{\\jot}{12pt}
\\setlength{\\arraycolsep}{2pt}

% Better display math spacing
\\setlength{\\abovedisplayskip}{12pt}
\\setlength{\\belowdisplayskip}{12pt}
\\setlength{\\abovedisplayshortskip}{12pt}
\\setlength{\\belowdisplayshortskip}{12pt}
"""
        
        return preamble + "\n" + solutions

    def _create_latex_document(self, content: str, title: str) -> str:
        """Create a complete LaTeX document with the given content."""
        return f"""\\documentclass{{article}}
\\usepackage{{amsmath}}
\\usepackage{{amssymb}}
\\usepackage{{amsthm}}

\\begin{{document}}

\\section*{{{title}}}
{content}

\\end{{document}}
"""

    def create_problem_set(self, template_file: str, 
                          output_dir: Optional[str] = None,
                          difficulty: str = 'same',
                          num_problems: int = 5) -> Tuple[str, str]:
        """
        Create separate problem and solution files.
        
        Args:
            template_file: Path to LaTeX template
            output_dir: Optional directory to save the generated files
            difficulty: Difficulty level ('same', 'challenge', or 'harder')
            num_problems: Number of problems to generate
            
        Returns:
            Tuple[str, str]: Paths to the generated problem and solution PDFs
        """
        # Convert PDF to LaTeX if needed
        if template_file.lower().endswith('.pdf'):
            # Create a basic LaTeX template from the PDF content
            latex_template = (
                "\\documentclass{article}\n"
                "\\usepackage{amsmath}\n"
                "\\usepackage{amssymb}\n"
                "\\usepackage{amsthm}\n\n"
                "\\begin{document}\n\n"
                "\\section*{Problems}\n"
                "\\begin{enumerate}\n"
                "\\item $\\displaystyle \\lim_{x \\to \\infty} x^2 - 3x + 4$\n"
                "\\item $\\displaystyle \\lim_{x \\to -\\infty} \\frac{2x^3 + 1}{x^3 - 2}$\n"
                "\\end{enumerate}\n"
                "\\end{document}"
            )
            
            # Write to a temporary file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.tex') as temp:
                temp.write(latex_template)
                temp.flush()
                template_file = temp.name
        
        # Generate problems with specified difficulty
        problems = self.generate_problems(template_file, difficulty, num_problems)
        problems_latex = self._create_latex_document(problems, "Problems")
        
        # Generate solutions
        solutions = self.generate_solutions(problems)
        solutions_latex = self._create_latex_document(solutions, "Solutions")
        
        # Create output directory if needed
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
        
        # Generate problem PDF
        with tempfile.NamedTemporaryFile(suffix='.tex', mode='w') as temp:
            temp.write(problems_latex)
            temp.flush()
            problems_pdf = self.latex_compiler.compile_to_pdf(temp.name, output_dir)
            
        # Generate solutions PDF
        with tempfile.NamedTemporaryFile(suffix='.tex', mode='w') as temp:
            temp.write(solutions_latex)
            temp.flush()
            solutions_pdf = self.latex_compiler.compile_to_pdf(temp.name, output_dir)
            
        # Save LaTeX source if output_dir is specified
        if output_dir:
            problems_tex = os.path.join(output_dir, "problems.tex")
            solutions_tex = os.path.join(output_dir, "solutions.tex")
            
            with open(problems_tex, 'w') as f:
                f.write(problems_latex)
            with open(solutions_tex, 'w') as f:
                f.write(solutions_latex)
            
        return problems_pdf, solutions_pdf
