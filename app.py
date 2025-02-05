from flask import Flask, request, jsonify, send_file, Response, stream_with_context
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, decode_token
from flask_bcrypt import Bcrypt
from flask_migrate import Migrate
from flask_cors import CORS
from datetime import datetime, timedelta
import os
import traceback
import logging
import tempfile
import queue
import threading
import json

from config import Config
from models.database import db, User, ProblemSet, GeneratedSet, DifficultyLevel, Provider
from utils.problem_generator import ProblemGenerator
from providers.claude_provider import ClaudeProvider
from providers.gemini_provider import GeminiProvider

app = Flask(__name__)
app.config.from_object(Config)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
)

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
bcrypt = Bcrypt(app)
migrate = Migrate(app, db)

# Configure CORS with more permissive settings for development
CORS(app, 
     origins=["http://localhost:3000"],
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     expose_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])

# JWT configuration
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)
app.config['JWT_TOKEN_LOCATION'] = ['headers']
app.config['JWT_HEADER_NAME'] = 'Authorization'
app.config['JWT_HEADER_TYPE'] = 'Bearer'

# Create tables
with app.app_context():
    db.create_all()

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Progress queue for SSE
progress_queues = {}

def send_progress(user_id: int, message: str):
    """Send a progress message to the user's queue."""
    app.logger.info(f"Sending progress for user {user_id}: {message}")
    if user_id not in progress_queues:
        app.logger.info(f"Creating new queue for user {user_id}")
        progress_queues[user_id] = queue.Queue()
    progress_queues[user_id].put({
        'type': 'progress',
        'message': message
    })

@app.route('/api/events')
def events():
    """SSE endpoint for progress updates."""
    token = request.args.get('token')
    app.logger.info("SSE connection attempt")
    if not token:
        app.logger.error("No token provided")
        return jsonify({'error': 'No token provided'}), 401
        
    try:
        # Verify and decode the token
        decoded_token = decode_token(token)
        user_id = int(decoded_token['sub'])
        app.logger.info(f"SSE connection established for user {user_id}")
        
        # Create queue for this user if it doesn't exist
        if user_id not in progress_queues:
            app.logger.info(f"Creating new queue for user {user_id} in events")
            progress_queues[user_id] = queue.Queue()
            # Send initial message
            progress_queues[user_id].put({
                'type': 'progress',
                'message': 'Connected to progress updates'
            })
        
        def generate():
            app.logger.info(f"Starting event stream for user {user_id}")
            try:
                while True:
                    try:
                        # Get message from queue, timeout after 30 seconds
                        msg = progress_queues[user_id].get(timeout=30)
                        app.logger.info(f"Sending message to user {user_id}: {msg}")
                        yield f"data: {json.dumps(msg)}\n\n"
                    except queue.Empty:
                        # Send ping to keep connection alive
                        app.logger.debug(f"Sending ping to user {user_id}")
                        yield f"data: {json.dumps({'type': 'ping'})}\n\n"
                    except KeyError:
                        # Queue was deleted, exit
                        app.logger.warning(f"Queue deleted for user {user_id}")
                        break
                        
            finally:
                # Cleanup when client disconnects
                app.logger.info(f"Client disconnected for user {user_id}")
                if user_id in progress_queues:
                    del progress_queues[user_id]
        
        return Response(
            stream_with_context(generate()),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': 'http://localhost:3000',
                'Access-Control-Allow-Credentials': 'true',
                'Content-Type': 'text/event-stream'
            }
        )
        
    except Exception as e:
        app.logger.error(f"SSE Error: {str(e)}")
        return jsonify({'error': 'Invalid token'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
        
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'Email already registered'}), 409
        
    hashed_password = bcrypt.generate_password_hash(data['password']).decode('utf-8')
    user = User(email=data['email'], password_hash=hashed_password)
    
    db.session.add(user)
    db.session.commit()
    
    # Convert user ID to string before creating token
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'token': access_token, 'user_id': user.id}), 201

@app.route('/api/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Missing email or password'}), 400
        
    user = User.query.filter_by(email=data['email']).first()
    if not user or not bcrypt.check_password_hash(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
        
    # Convert user ID to string before creating token
    access_token = create_access_token(identity=str(user.id))
    return jsonify({'token': access_token, 'user_id': user.id}), 200

@app.route('/api/problem-sets', methods=['POST'])
@jwt_required()
def create_problem_set():
    try:
        # Convert user ID from string back to integer
        user_id = int(get_jwt_identity())
        app.logger.info(f"Creating problem set for user {user_id}")
        
        if 'file' in request.files:
            app.logger.info("Processing file upload")
            file = request.files['file']
            app.logger.info(f"Received file: {file.filename}")
            
            if file.filename == '':
                app.logger.warning("No file selected")
                return jsonify({'error': 'No file selected'}), 400
                
            if not file.filename.lower().endswith('.pdf'):
                app.logger.warning(f"Invalid file type: {file.filename}")
                return jsonify({'error': 'Only PDF files are allowed'}), 400
            
            try:
                # Save the uploaded file
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{file.filename}"
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                app.logger.info(f"Saving file to: {filepath}")
                file.save(filepath)
                app.logger.info("File saved successfully")
                
                # Extract LaTeX from PDF
                app.logger.info("Extracting LaTeX from PDF")
                generator = ProblemGenerator(ClaudeProvider())  # Use Claude for better LaTeX conversion
                latex_template = generator.extract_latex_from_pdf(filepath)
                app.logger.info("LaTeX template extracted successfully")
                
                name = request.form.get('name', file.filename.replace('.pdf', ''))
                app.logger.info(f"Using name: {name}")
                
                if not name or not isinstance(name, str):
                    return jsonify({'error': 'Name must be a string'}), 422
                
                problem_set = ProblemSet(
                    user_id=user_id,
                    name=name,
                    original_pdf_path=filepath,
                    latex_template=latex_template  # Save the extracted LaTeX
                )
                
            except Exception as e:
                app.logger.error(f"Error processing file: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
                return jsonify({'error': f'Error processing file: {str(e)}'}), 500
                
        else:
            app.logger.info("Processing LaTeX template submission")
            data = request.get_json()
            
            if not data or not data.get('name') or not data.get('template'):
                return jsonify({'error': 'Missing name or template'}), 400
                
            name = data['name']
            latex_template = data['template']
            
            if not isinstance(name, str) or not isinstance(latex_template, str):
                return jsonify({'error': 'Name and template must be strings'}), 422
                
            problem_set = ProblemSet(
                user_id=user_id,
                name=name,
                latex_template=latex_template
            )
        
        try:
            db.session.add(problem_set)
            db.session.commit()
            app.logger.info(f"Problem set created with ID: {problem_set.id}")
            
            return jsonify({
                'id': problem_set.id,
                'name': problem_set.name,
                'created_at': problem_set.created_at.isoformat(),
                'generated_sets_count': len(problem_set.generated_sets)
            }), 201
            
        except Exception as e:
            app.logger.error(f"Database error: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
            db.session.rollback()
            return jsonify({'error': f'Database error: {str(e)}'}), 500
        
    except ValueError as e:
        app.logger.error(f"Invalid user ID format: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
        return jsonify({'error': 'Invalid user ID format'}), 400
    except Exception as e:
        app.logger.error(f"Error creating problem set: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
        return jsonify({'error': f'Error creating problem set: {str(e)}'}), 500

@app.route('/api/problem-sets', methods=['GET'])
@jwt_required()
def get_problem_sets():
    try:
        # Convert user ID from string back to integer
        user_id = int(get_jwt_identity())
        app.logger.info(f"Fetching problem sets for user {user_id}")
        
        problem_sets = ProblemSet.query.filter_by(user_id=user_id).all()
        
        return jsonify([{
            'id': ps.id,
            'name': ps.name,
            'created_at': ps.created_at.isoformat(),
            'generated_sets_count': len(ps.generated_sets)
        } for ps in problem_sets]), 200
        
    except ValueError as e:
        app.logger.error(f"Invalid user ID format: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
        return jsonify({'error': 'Invalid user ID format'}), 400
    except Exception as e:
        app.logger.error(f"Error fetching problem sets: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
        return jsonify({'error': f'Error fetching problem sets: {str(e)}'}), 500

@app.route('/api/problem-sets/<int:set_id>/generate', methods=['POST'])
@jwt_required()
def generate_problems(set_id):
    try:
        # Convert user ID from string back to integer
        user_id = int(get_jwt_identity())
        app.logger.info(f"Generating problems for set {set_id}")
        
        problem_set = ProblemSet.query.filter_by(id=set_id, user_id=user_id).first()
        if not problem_set:
            return jsonify({'error': 'Problem set not found'}), 404
            
        if not problem_set.latex_template:
            app.logger.error(f"Problem set {set_id} has no LaTeX template")
            return jsonify({'error': 'Problem set has no LaTeX template'}), 400
            
        data = request.get_json()
        app.logger.info(f"Received data: {data}")
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        provider_name = data.get('provider')
        difficulty = data.get('difficulty')
        num_problems = data.get('num_problems')
        
        app.logger.info(f"Extracted values - provider: {provider_name}, difficulty: {difficulty}, num_problems: {num_problems}")
        
        # Validate required fields
        if not provider_name or not difficulty or not num_problems:
            missing = []
            if not provider_name: missing.append('provider')
            if not difficulty: missing.append('difficulty')
            if not num_problems: missing.append('num_problems')
            error_msg = f"Missing required fields: {', '.join(missing)}"
            app.logger.error(error_msg)
            return jsonify({'error': error_msg}), 400
            
        # Validate provider
        if provider_name.lower() not in ['claude', 'gemini']:
            return jsonify({'error': 'Invalid provider. Must be "claude" or "gemini"'}), 400
            
        # Create provider instance
        provider = ClaudeProvider() if provider_name.lower() == 'claude' else GeminiProvider()
        
        # Create output directory for this generation
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = os.path.join(app.config['UPLOAD_FOLDER'], f'generated_{timestamp}')
        os.makedirs(output_dir, exist_ok=True)
        
        # Write template to a temporary file
        template_file = os.path.join(output_dir, 'template.tex')
        with open(template_file, 'w') as f:
            f.write(problem_set.latex_template)
        
        # Generate problems and solutions
        generator = ProblemGenerator(provider)
        try:
            # Step 1: Generate problems
            send_progress(user_id, "Generating problems...")
            problems = generator.generate_problems(template_file, difficulty, num_problems)
            problems_latex = generator._create_latex_document(problems, "Problems")
            
            # Step 2: Generate solutions
            send_progress(user_id, "Generating solutions...")
            solutions = generator.generate_solutions(problems)
            solutions_latex = generator._create_latex_document(solutions, "Solutions")
            
            # Step 3: Compile problems PDF
            send_progress(user_id, "Compiling problems PDF...")
            with tempfile.NamedTemporaryFile(suffix='.tex', mode='w') as temp:
                temp.write(problems_latex)
                temp.flush()
                problems_pdf = generator.latex_compiler.compile_to_pdf(temp.name, output_dir)
            
            # Step 4: Compile solutions PDF
            send_progress(user_id, "Compiling solutions PDF...")
            with tempfile.NamedTemporaryFile(suffix='.tex', mode='w') as temp:
                temp.write(solutions_latex)
                temp.flush()
                solutions_pdf = generator.latex_compiler.compile_to_pdf(temp.name, output_dir)
            
            send_progress(user_id, "Generation complete!")
            
            # Create new generated set record
            generated_set = GeneratedSet(
                problem_set_id=set_id,
                provider=Provider[provider_name.upper()],
                difficulty=DifficultyLevel[difficulty.upper()],
                num_problems=num_problems,
                problems_pdf_path=problems_pdf,
                solutions_pdf_path=solutions_pdf,
                problems_latex=problems_latex,
                solutions_latex=solutions_latex
            )
            
            db.session.add(generated_set)
            db.session.commit()
            
            return jsonify({
                'id': generated_set.id,
                'created_at': generated_set.created_at.isoformat(),
                'problems_path': generated_set.problems_pdf_path,
                'solutions_path': generated_set.solutions_pdf_path
            }), 201
            
        except Exception as e:
            app.logger.error(f"Error generating problems: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
            send_progress(user_id, f"Error: {str(e)}")
            return jsonify({'error': str(e)}), 500
            
    except ValueError as e:
        app.logger.error(f"Invalid user ID format: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
        return jsonify({'error': 'Invalid user ID format'}), 400
    except Exception as e:
        app.logger.error(f"Error generating problems: {str(e)}\n{''.join(traceback.format_tb(e.__traceback__))}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/problem-sets/<int:set_id>/generated', methods=['GET'])
@jwt_required()
def get_generated_sets(set_id):
    user_id = int(get_jwt_identity())
    
    # Get all generated sets for this problem set
    generated_sets = GeneratedSet.query.join(ProblemSet).filter(
        ProblemSet.id == set_id,
        ProblemSet.user_id == user_id
    ).order_by(GeneratedSet.created_at.desc()).all()
    
    return jsonify([{
        'id': set.id,
        'created_at': set.created_at.isoformat(),
        'provider': set.provider.value,
        'difficulty': set.difficulty.value,
        'num_problems': set.num_problems,
        'problems_path': set.problems_pdf_path,
        'solutions_path': set.solutions_pdf_path
    } for set in generated_sets])

@app.route('/api/generated-sets/<int:set_id>/download', methods=['GET'])
@jwt_required()
def download_generated_set(set_id):
    # Convert user ID from string back to integer
    user_id = int(get_jwt_identity())
    generated_set = GeneratedSet.query.join(ProblemSet).filter(
        GeneratedSet.id == set_id,
        ProblemSet.user_id == user_id
    ).first()
    
    if not generated_set:
        return jsonify({'error': 'Generated set not found'}), 404
    
    file_type = request.args.get('type', 'problems')  # or 'solutions'
    pdf_path = generated_set.problems_pdf_path if file_type == 'problems' else generated_set.solutions_pdf_path
    
    return send_file(pdf_path, as_attachment=True)

if __name__ == '__main__':
    app.run(port=8081, debug=True)
