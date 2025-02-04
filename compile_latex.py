#!/usr/bin/env python3
import argparse
import os
from rich.console import Console
from utils.latex_compiler import LatexCompiler

console = Console()

def setup_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description='Compile LaTeX files to PDF using Tectonic'
    )
    parser.add_argument('input',
                       help='Input .tex file')
    parser.add_argument('--output-dir',
                       help='Output directory for the PDF (optional)')
    return parser

def main():
    args = setup_args().parse_args()
    
    try:
        compiler = LatexCompiler()
        console.print(f"[yellow]Compiling {args.input} with Tectonic...[/yellow]")
        
        pdf_path = compiler.compile_to_pdf(
            args.input,
            output_dir=args.output_dir
        )
        
        console.print(f"[green]✓ PDF generated successfully: {pdf_path}[/green]")
        
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
