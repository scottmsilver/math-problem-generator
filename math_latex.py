#!/usr/bin/env python3
import argparse
import os
import sys
from typing import Optional
from rich.console import Console
import tempfile
from pylatex import Document, Package
from providers.claude_provider import ClaudeProvider
from providers.gemini_provider import GeminiProvider
from utils.logger import setup_logging

console = Console()

class MathLatexConverter:
    def __init__(self, provider, log_dir: str):
        self.provider = provider
        self.log_dir = log_dir
        self.logger = setup_logging(log_dir)

    def convert_to_latex(self, file_path: str) -> str:
        """Convert a math problem from PDF/image to LaTeX."""
        with open('latex_prompt.txt', 'r') as file:
            prompt = file.read()
        
        latex = self.provider.execute(prompt, [file_path])
        self.logger.log_interaction(
            model=self.provider.__class__.__name__,
            prompt=prompt,
            response=latex,
            images=[file_path],
            variables={}  # Add empty variables dict
        )
        return latex

    def validate_conversion(self, original_file: str, latex_content: str) -> bool:
        """Validate the conversion by comparing with LLM."""
        prompt = (
            "Compare this LaTeX code with the content in the document. Are they mathematically equivalent?\n\n"
            f"LaTeX Code:\n{latex_content}\n\n"
            "Consider:\n"
            "1. Mathematical expressions and symbols\n"
            "2. Layout and structure\n"
            "3. Text content and context\n"
            "Answer with ONLY 'yes' or 'no'."
        )
        
        result = self.provider.execute(prompt, [original_file])
        self.logger.log_interaction(
            model=self.provider.__class__.__name__,
            prompt=prompt,
            response=result,
            images=[original_file],
            variables={}
        )
        return result.strip().lower() == 'yes'

def setup_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Convert math problems from PDF/image to LaTeX'
    )
    parser.add_argument('--model', choices=['gemini', 'claude'], required=True,
                       help='Model to use for conversion')
    parser.add_argument('--input', required=True,
                       help='Input PDF or image file')
    parser.add_argument('--log-dir', required=True,
                       help='Directory to store logs')
    parser.add_argument('--validate', action='store_true',
                       help='Validate the conversion by rendering and comparing')
    parser.add_argument('--output',
                       help='Output file for the LaTeX code (optional)')
    return parser

def main():
    args = setup_args().parse_args()
    
    # Initialize provider
    provider = ClaudeProvider() if args.model == 'claude' else GeminiProvider()
    converter = MathLatexConverter(provider, args.log_dir)
    
    try:
        # Convert to LaTeX
        latex = converter.convert_to_latex(args.input)
        
        # Save or display output
        if args.output:
            with open(args.output, 'w') as f:
                f.write(latex)
            console.print(f"[green]LaTeX code saved to: {args.output}[/green]")
        else:
            console.print("[green]LaTeX Code:[/green]")
            console.print(latex)
        
        # Validate if requested
        if args.validate:
            console.print("\n[yellow]Validating conversion...[/yellow]")
            if converter.validate_conversion(args.input, latex):
                console.print("[green]✓ Conversion validated successfully[/green]")
            else:
                console.print("[red]⚠ Conversion may not be accurate[/red]")
                
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
