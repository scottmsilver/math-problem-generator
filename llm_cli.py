#!/usr/bin/env python3
import argparse
import os
import sys
from typing import Dict, List, Optional
from rich.console import Console
from rich import print as rprint

from providers.claude_provider import ClaudeProvider
from providers.gemini_provider import GeminiProvider
from utils.image_handler import validate_image_paths
from utils.logger import setup_logging
from utils.prompt_handler import PromptHandler

console = Console()

def setup_args() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='LLM CLI Tool for Gemini and Claude')
    parser.add_argument('--model', choices=['gemini', 'claude'], required=True,
                       help='Choose the LLM model to use')
    parser.add_argument('--prompt', required=True,
                       help='Prompt template to use')
    parser.add_argument('--vars', nargs='*', default=[],
                       help='Named arguments for the prompt template in key=value format')
    parser.add_argument('--images', nargs='*', default=[],
                       help='Paths to image files to include')
    parser.add_argument('--log-dir', required=True,
                       help='Directory to store logs')
    return parser

def parse_vars(var_list: List[str]) -> Dict[str, str]:
    result = {}
    for var in var_list:
        try:
            key, value = var.split('=', 1)
            result[key.strip()] = value.strip()
        except ValueError:
            console.print(f"[red]Error: Invalid variable format '{var}'. Use key=value format.[/red]")
            sys.exit(1)
    return result

def main():
    parser = setup_args()
    args = parser.parse_args()

    # Setup logging
    logger = setup_logging(args.log_dir)

    # Validate and process images
    if args.images:
        try:
            validate_image_paths(args.images)
        except ValueError as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            sys.exit(1)

    # Parse template variables
    template_vars = parse_vars(args.vars)

    # Initialize prompt handler
    prompt_handler = PromptHandler()

    try:
        # Process prompt template
        final_prompt = prompt_handler.process_template(args.prompt, template_vars)
        
        # Initialize appropriate provider
        if args.model == 'claude':
            provider = ClaudeProvider()
        else:
            provider = GeminiProvider()

        # Execute the prompt
        response = provider.execute(
            prompt=final_prompt,
            image_paths=args.images
        )

        # Log the interaction
        logger.log_interaction(
            model=args.model,
            prompt=final_prompt,
            variables=template_vars,
            images=args.images,
            response=response
        )

        # Display the response
        console.print("\n[green]Response:[/green]")
        console.print(response)

    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()
