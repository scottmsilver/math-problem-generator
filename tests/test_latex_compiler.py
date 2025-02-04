import os
import pytest
from pathlib import Path
from utils.latex_compiler import LatexCompiler

@pytest.fixture
def compiler():
    return LatexCompiler()

@pytest.fixture
def sample_tex_file(tmp_path):
    tex_content = r"""
\documentclass{article}
\usepackage{amsmath}
\usepackage{amssymb}

\begin{document}
\section*{Sample Math Document}

Here's a simple equation:
\[ E = mc^2 \]

And a more complex one:
\[ \int_{-\infty}^{\infty} e^{-x^2} dx = \sqrt{\pi} \]

\end{document}
"""
    tex_file = tmp_path / "sample.tex"
    tex_file.write_text(tex_content)
    return str(tex_file)

@pytest.fixture
def limits_tex_file():
    # Use the existing limits.tex file
    tex_file = Path("limits.tex")
    assert tex_file.exists(), "limits.tex file not found"
    return str(tex_file)

def test_compile_simple_document(compiler, sample_tex_file, tmp_path):
    output_dir = str(tmp_path / "output")
    pdf_path = compiler.compile_to_pdf(sample_tex_file, output_dir)
    
    assert os.path.exists(pdf_path)
    assert pdf_path.endswith('.pdf')
    assert os.path.getsize(pdf_path) > 0

def test_compile_limits_document(compiler, limits_tex_file, tmp_path):
    output_dir = str(tmp_path / "output")
    pdf_path = compiler.compile_to_pdf(limits_tex_file, output_dir)
    
    assert os.path.exists(pdf_path)
    assert pdf_path.endswith('.pdf')
    assert os.path.getsize(pdf_path) > 0

def test_nonexistent_file(compiler):
    with pytest.raises(FileNotFoundError):
        compiler.compile_to_pdf("nonexistent.tex")

def test_invalid_latex(tmp_path):
    # Create a tex file with invalid LaTeX
    invalid_tex = tmp_path / "invalid.tex"
    invalid_tex.write_text(r"""
\documentclass{article}
\begin{document}
\invalid_command
\end{document}
""")
    
    compiler = LatexCompiler()
    with pytest.raises(RuntimeError):
        compiler.compile_to_pdf(str(invalid_tex))
