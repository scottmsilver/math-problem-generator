from providers import LLMProvider

class MockProvider(LLMProvider):
    """Mock provider for testing that returns predefined responses."""
    
    def __init__(self, problems_response: str = None, solutions_response: str = None):
        self.problems_response = problems_response or self._default_problems()
        self.solutions_response = solutions_response or self._default_solutions()
        self.last_prompt = None
        
    def execute(self, prompt: str, file_paths=None) -> str:
        """Return predefined response based on prompt content."""
        self.last_prompt = prompt
        if "Generate solutions" in prompt or "Generate detailed solutions" in prompt:
            return self.solutions_response
        return self.problems_response
        
    def _default_problems(self) -> str:
        return r"""\begin{enumerate}
\item $\displaystyle \lim_{x \to \infty} 3x^2 - 2x + 1$
\item $\displaystyle \lim_{x \to -\infty} \frac{x^3 + 2}{x^2 - 1}$
\item \textbf{[Challenge]} $\displaystyle \lim_{x \to \infty} \frac{\sin(x)}{x}$
\end{enumerate}"""
        
    def _default_solutions(self) -> str:
        return r"""Solution:
$\displaystyle \lim_{x \to \infty} 3x^2 - 2x + 1$
\begin{align*}
&= \lim_{x \to \infty} x^2(3 - \frac{2}{x} + \frac{1}{x^2}) \\
&= \infty \cdot (3 - 0 + 0) \\
&= \boxed{\infty}
\end{align*}

Solution:
$\displaystyle \lim_{x \to -\infty} \frac{x^3 + 2}{x^2 - 1}$
\begin{align*}
&= \lim_{x \to -\infty} \frac{x^3(1 + \frac{2}{x^3})}{x^2(1 - \frac{1}{x^2})} \\
&= \lim_{x \to -\infty} x \cdot \frac{1 + 0}{1 - 0} \\
&= \boxed{-\infty}
\end{align*}

Solution:
$\displaystyle \lim_{x \to \infty} \frac{\sin(x)}{x}$
\begin{align*}
&= \boxed{0} \quad \text{(by the Squeeze Theorem)}
\end{align*}"""
