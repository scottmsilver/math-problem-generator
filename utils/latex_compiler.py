import os
import subprocess
import shutil
from pathlib import Path
from typing import Optional

class LatexCompiler:
    def __init__(self):
        """Initialize the LaTeX compiler."""
        # Check if tectonic is available
        self.tectonic_path = shutil.which('tectonic')
        if not self.tectonic_path:
            raise RuntimeError("Tectonic not found. Please install it with 'brew install tectonic'")
        
    def compile_to_pdf(self, tex_file: str, output_dir: Optional[str] = None) -> str:
        """Compile a LaTeX file to PDF using Tectonic.
        
        Args:
            tex_file: Path to the .tex file
            output_dir: Directory to save the PDF (default: same as tex_file)
            
        Returns:
            str: Path to the generated PDF file
        """
        tex_path = Path(tex_file)
        if not tex_path.exists():
            raise FileNotFoundError(f"LaTeX file not found: {tex_file}")
            
        if output_dir:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
        else:
            output_path = tex_path.parent
            
        # Get the base name without extension
        base_name = tex_path.stem
        
        try:
            # Run tectonic
            result = subprocess.run(
                [self.tectonic_path, str(tex_path)],
                cwd=str(tex_path.parent),
                capture_output=True,
                text=True,
                check=True
            )
            
            # Get the generated PDF path
            temp_pdf = str(tex_path).replace(".tex", ".pdf")
            
            # Move PDF to output directory if specified
            if output_dir:
                final_pdf = os.path.join(output_dir, f"{base_name}.pdf")
                shutil.move(temp_pdf, final_pdf)
                return final_pdf
                
            # Otherwise return the PDF in the original directory
            return temp_pdf
                
        except subprocess.CalledProcessError as e:
            error_msg = e.stderr if e.stderr else e.stdout
            raise RuntimeError(f"Tectonic compilation failed:\n{error_msg}")
