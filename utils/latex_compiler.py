import os
import subprocess
import tempfile
import shutil
from pathlib import Path
from typing import Optional

class LatexCompiler:
    def __init__(self):
        # Check if tectonic is available
        self.tectonic_path = shutil.which('tectonic')
        if not self.tectonic_path:
            raise RuntimeError("Tectonic not found. Please install it with 'brew install tectonic'")
        
    def compile_to_pdf(self, tex_file: str, output_dir: Optional[str] = None) -> str:
        """
        Compile a LaTeX file to PDF using Tectonic.
        
        Args:
            tex_file: Path to the .tex file
            output_dir: Directory to save the PDF (default: same as tex_file)
            
        Returns:
            str: Path to the generated PDF file
        
        Raises:
            RuntimeError: If compilation fails
            FileNotFoundError: If tex_file doesn't exist
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
        
        # Create a temporary directory for compilation
        with tempfile.TemporaryDirectory() as tmpdir:
            # Copy tex file to temp dir
            temp_tex = Path(tmpdir) / tex_path.name
            shutil.copy2(tex_path, temp_tex)
            
            try:
                # Run tectonic
                result = subprocess.run(
                    [self.tectonic_path, str(temp_tex)],
                    cwd=tmpdir,
                    capture_output=True,
                    text=True,
                    check=True
                )
                
                # Get the generated PDF path
                temp_pdf = str(temp_tex).replace(".tex", ".pdf")
                
                # Move PDF to output directory
                if output_dir:
                    final_pdf = os.path.join(output_dir, f"{base_name}.pdf")
                    shutil.move(temp_pdf, final_pdf)
                    return final_pdf
                    
                # Move PDF to original directory
                output_pdf = output_path / f"{base_name}.pdf"
                shutil.move(temp_pdf, output_pdf)
                return str(output_pdf)
                    
            except subprocess.CalledProcessError as e:
                error_msg = e.stderr if e.stderr else e.stdout
                raise RuntimeError(f"Tectonic compilation failed:\n{error_msg}")
