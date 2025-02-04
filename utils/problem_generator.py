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
        
    def generate_problems(self, template_file: str, num_problems: int = 5,
                         difficulty: str = "similar") -> str:
        """
        Generate new problems similar to those in the template.
        
        Args:
            template_file: Path to LaTeX template file
            num_problems: Number of problems to generate
            difficulty: "easier", "similar", "harder", or "challenge"
            
        Returns:
            str: LaTeX code containing the generated problems
        """
        with open(template_file, 'r') as f:
            template = f.read()
            
        prompt = (
            f"Study this LaTeX document containing math problems.\n"
            f"Generate {num_problems} new problems that are {difficulty} in difficulty "
            f"than the template problems, while maintaining a similar style and format.\n\n"
            "Rules:\n"
            "1. Keep the same LaTeX structure and environments\n"
            "2. Use proper LaTeX notation (e.g., use '^{2}' not '²' for superscripts)\n"
            "3. Ensure problems are mathematically correct\n"
            "4. Return ONLY the LaTeX code for the new problems\n"
            "5. Do NOT include solutions\n"
            "6. Use \\begin{enumerate} for the problems\n"
            "7. Each problem should be complete and self-contained\n"
            "8. Use \\displaystyle for all limits\n"
            "9. Format all math in proper LaTeX dollar signs\n"
        )
        
        problems = self.provider.execute(prompt, [template_file])
        return problems
        
    def generate_solutions(self, problems_latex: str) -> str:
        """
        Generate detailed solutions for a set of problems.
        
        Args:
            problems_latex: LaTeX code containing the problems
            
        Returns:
            str: LaTeX code containing the worked-out solutions
        """
        # Write problems to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex') as temp:
            temp.write(problems_latex)
            temp.flush()
            
            prompt = (
                "Generate detailed, worked-out solutions for these math problems.\n"
                "Rules:\n"
                "1. Format each solution with clear spacing and organization:\n"
                "   - Begin each solution with 'Solution:' followed by the original problem in display math\n"
                "   - Put each step on a separate line using the align* environment\n"
                "   - Add proper spacing around operators (\\;, \\quad)\n"
                "   - Never combine multiple steps on one line\n"
                "   - Add explanatory text between major steps\n\n"
                "2. For algebraic manipulations:\n"
                "   - Use \\left( and \\right) for proper parenthesis sizing\n"
                "   - Use \\dfrac instead of \\frac for main-line fractions\n"
                "   - Align numerators and denominators cleanly\n"
                "   - Show each algebraic step on its own line with &= alignment\n\n"
                "3. For limits with fractions:\n"
                "   - Factor out highest powers of x clearly\n"
                "   - Show the factored form on a separate line\n"
                "   - Keep limit evaluations of separate parts distinct\n"
                "   - Use proper grouping with \\left( and \\right) when splitting limits\n"
                "   - Use \\limit{x \\to a} instead of \\lim_{x \\to a}\n\n"
                "4. For final evaluations:\n"
                "   - Break down steps leading to infinity or numerical results\n"
                "   - Show multiplication with infinity clearly (e.g., '\\infinity \\cdot 4')\n"
                "   - Show reduction of fractions to simplest form\n"
                "   - Use \\infinity instead of \\infty\n\n"
                "5. For limit notation:\n"
                "   - Use \\limit{x \\to a} macro for consistent spacing\n"
                "   - Use \\infinity macro for proper infinity symbol\n"
                "   - Add \\; before arrows\n"
                "   - Use \\to instead of \\rightarrow\n\n"
                "6. Use proper LaTeX environments:\n"
                "   - Begin each solution with \\textbf{Solution:}\n"
                "   - Use align* environment for sequential steps\n"
                "   - Add \\quad before explanatory text\n"
                "   - Number solutions to match problem numbers\n"
                "   - Add blank line between solutions\n"
            )
            
            solutions = self.provider.execute(prompt, [temp.name])
            
            # Add LaTeX preamble for better math formatting
            preamble = (
                "% Custom spacing for limit notation\n"
                "\\def\\limit#1{\\lim\\limits_{#1}\\;}\n"
                "\\def\\infinity{\\infty}\n\n"
                "% Better fraction spacing\n"
                "\\setlength{\\jot}{12pt}\n"
                "\\setlength{\\arraycolsep}{2pt}\n\n"
                "% Better display math spacing\n"
                "\\setlength{\\abovedisplayskip}{12pt}\n"
                "\\setlength{\\belowdisplayskip}{12pt}\n"
                "\\setlength{\\abovedisplayshortskip}{12pt}\n"
                "\\setlength{\\belowdisplayshortskip}{12pt}\n\n"
            )
            
            return preamble + solutions

    def _create_latex_document(self, content: str, title: str) -> str:
        """Create a complete LaTeX document with the given content."""
        return (
            "\\documentclass{article}\n"
            "\\usepackage{amsmath}\n"
            "\\usepackage{amssymb}\n"
            "\\usepackage{amsthm}\n\n"
            "\\begin{document}\n\n"
            f"\\section*{{{title}}}\n"
            f"{content}\n\n"
            "\\end{document}"
        )
        
    def create_problem_set(self, template_file: str, 
                          output_dir: Optional[str] = None) -> Tuple[str, str]:
        """
        Create separate problem and solution files.
        
        Args:
            template_file: Path to LaTeX template
            output_dir: Optional directory to save the generated files
            
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
        
        # Generate problems
        problems = self.generate_problems(template_file)
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
