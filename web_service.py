import os
import tempfile
import zipfile
import json
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from flask import Flask, request, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from utils.problem_generator import ProblemGenerator
from providers.claude_provider import ClaudeProvider
from providers.gemini_provider import GeminiProvider

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create output directory for PDFs
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(OUTPUT_DIR, exist_ok=True)

def get_provider(provider_name):
    """Get the appropriate LLM provider instance."""
    if provider_name == "gemini":
        return GeminiProvider()
    return ClaudeProvider()

def create_zip_response(problems_pdf, solutions_pdf, problems_tex, solutions_tex, original_pdf=None):
    """Create a zip file containing all generated files."""
    memory_file = BytesIO()
    with zipfile.ZipFile(memory_file, 'w', zipfile.ZIP_DEFLATED) as zf:
        # Add PDF files
        zf.write(problems_pdf, "problems.pdf")
        zf.write(solutions_pdf, "solutions.pdf")
        
        # Add LaTeX source files
        zf.write(problems_tex, "problems.tex")
        zf.write(solutions_tex, "solutions.tex")
        
        # Add original PDF if provided
        if original_pdf:
            zf.write(original_pdf, "original.pdf")
        
        # Add metadata
        files = [
            {"name": "problems.pdf", "type": "pdf", "description": "Generated problems in PDF format"},
            {"name": "solutions.pdf", "type": "pdf", "description": "Generated solutions in PDF format"},
            {"name": "problems.tex", "type": "tex", "description": "LaTeX source for problems"},
            {"name": "solutions.tex", "type": "tex", "description": "LaTeX source for solutions"}
        ]
        if original_pdf:
            files.append({"name": "original.pdf", "type": "pdf", "description": "Original uploaded PDF"})
            
        metadata = {
            "generated_at": datetime.now().isoformat(),
            "files": files
        }
        zf.writestr("metadata.json", json.dumps(metadata, indent=2))
    
    memory_file.seek(0)
    return memory_file

def extract_text_from_pdf(pdf_file):
    """Extract text content from a PDF file."""
    reader = PdfReader(pdf_file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() + "\n"
    return text

def convert_to_latex_template(text):
    """Convert extracted text to a LaTeX template."""
    return f"""\\documentclass{{article}}
\\begin{{document}}
\\begin{{enumerate}}
{text}
\\end{{enumerate}}
\\end{{document}}
"""

@app.route("/generate", methods=["POST"])
def generate_problems():
    """Generate math problems and solutions based on the template."""
    try:
        # Check if file is uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file.filename == '':
                return jsonify({"error": "No file selected"}), 400
                
            if not file.filename.lower().endswith('.pdf'):
                return jsonify({"error": "Only PDF files are allowed"}), 400
            
            # Save uploaded file temporarily
            temp_pdf = os.path.join(OUTPUT_DIR, secure_filename(file.filename))
            file.save(temp_pdf)
            
            # Extract text and create template
            text = extract_text_from_pdf(temp_pdf)
            template_content = convert_to_latex_template(text)
            
        else:
            # Handle JSON input
            data = request.get_json()
            if not data or "template_content" not in data:
                return jsonify({"error": "Either a PDF file or template_content is required"}), 400
            template_content = data["template_content"]
            temp_pdf = None
            
        # Get optional parameters with defaults
        provider_name = request.form.get("provider", "claude") if 'file' in request.files else request.json.get("provider", "claude")
        difficulty = request.form.get("difficulty", "same") if 'file' in request.files else request.json.get("difficulty", "same")
        num_problems = request.form.get("num_problems", 5) if 'file' in request.files else request.json.get("num_problems", 5)
        
        # Validate difficulty
        if difficulty not in ["same", "challenge", "harder"]:
            return jsonify({"error": "Invalid difficulty level"}), 400
            
        # Validate num_problems
        try:
            num_problems = int(num_problems)
            if num_problems < 1 or num_problems > 20:
                return jsonify({"error": "num_problems must be between 1 and 20"}), 400
        except ValueError:
            return jsonify({"error": "num_problems must be an integer"}), 400
            
        # Create temporary template file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.tex') as temp:
            temp.write(template_content)
            temp.flush()
            
            # Initialize provider and generator
            provider = get_provider(provider_name)
            generator = ProblemGenerator(provider)
            
            # Generate problems and solutions
            problems_pdf, solutions_pdf = generator.create_problem_set(
                temp.name,
                output_dir=OUTPUT_DIR,
                difficulty=difficulty,
                num_problems=num_problems
            )
            
            # Get LaTeX source files
            problems_tex = os.path.join(OUTPUT_DIR, "problems.tex")
            solutions_tex = os.path.join(OUTPUT_DIR, "solutions.tex")
            
            # Create zip file with all generated content
            zip_buffer = create_zip_response(
                problems_pdf,
                solutions_pdf,
                problems_tex,
                solutions_tex,
                temp_pdf
            )
            
            # Generate a filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"math_problems_{timestamp}.zip"
            
            return send_file(
                zip_buffer,
                mimetype='application/zip',
                as_attachment=True,
                download_name=filename
            )
            
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up temporary PDF file if it exists
        if 'temp_pdf' in locals() and temp_pdf:
            try:
                os.remove(temp_pdf)
            except:
                pass

if __name__ == "__main__":
    # Get port from environment or use default
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port, debug=True)
