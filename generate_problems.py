#!/usr/bin/env python3
import argparse
import os
from rich.console import Console
from utils.problem_generator import ProblemGenerator
from providers.claude_provider import ClaudeProvider
from providers.gemini_provider import GeminiProvider

console = Console()

def setup_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Generate math problems similar to a template'
    )
    parser.add_argument('template',
                       help='Input LaTeX template file')
    parser.add_argument('--output-dir',
                       help='Output directory for generated files')
    parser.add_argument('--provider', choices=['claude', 'gemini'],
                       default='claude',
                       help='LLM provider to use (default: claude)')
    return parser

def main():
    args = setup_args().parse_args()
    
    try:
        # Select provider
        if args.provider == 'gemini':
            provider = GeminiProvider()
        else:
            provider = ClaudeProvider()
            
        generator = ProblemGenerator(provider)
        
        console.print(f"[yellow]Generating problems and solutions using {args.provider}...[/yellow]")
        
        problems_pdf, solutions_pdf = generator.create_problem_set(
            args.template,
            output_dir=args.output_dir
        )
        
        console.print(f"[green]✓ Generated problems saved to: {problems_pdf}[/green]")
        console.print(f"[green]✓ Generated solutions saved to: {solutions_pdf}[/green]")
        
        if args.output_dir:
            problems_tex = os.path.join(args.output_dir, "problems.tex")
            solutions_tex = os.path.join(args.output_dir, "solutions.tex")
            console.print(f"[green]✓ LaTeX sources saved to: {problems_tex} and {solutions_tex}[/green]")
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
